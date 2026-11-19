import argparse
import asyncio
import csv
import os
import statistics
import time
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from benchmark.adverts_repo_orm import  OrmAdvertsRepository
from models.advert import Advert
from repositories.advert_repository import AdvertsRepository

from sql_builders.advert_sql_builder import AdvertsSqlBuilder

# Фиксированные тестовые UUID для изоляции тестовых данных
TEST_PROFILE_ID = UUID("11111111-1111-1111-1111-111111111111")
TEST_SELLER_ID = UUID("22222222-2222-2222-2222-222222222222")
TEST_CATEGORY_ID = UUID("33333333-3333-3333-3333-333333333333")


def measure_timer_overhead(iterations: int = 10_000) -> float:
    """Измерение собственной погрешности (overhead) таймера в наносекундах."""
    samples = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        t1 = time.perf_counter_ns()
        samples.append(t1 - t0)
    return statistics.median(samples)


async def setup_test_entities(session: AsyncSession) -> None:
    """Создаем минимально необходимые записи для внешних ключей (профиль, продавец, категория)."""
    await session.execute(
        text("""
            INSERT INTO adv_uuid.profiles (id, nickname, fio, email, password)
            VALUES (:pid, 'bench_user', 'Benchmark User', 'bench@test.local', 'bench_pass')
            ON CONFLICT (id) DO NOTHING
        """),
        {"pid": TEST_PROFILE_ID},
    )
    await session.execute(
        text("""
            INSERT INTO adv_uuid.sellers (id, profile_id)
            VALUES (:sid, :pid)
            ON CONFLICT (id) DO NOTHING
        """),
        {"sid": TEST_SELLER_ID, "pid": TEST_PROFILE_ID},
    )
    await session.execute(
        text("""
            INSERT INTO adv_uuid.categories (id, name)
            VALUES (:cid, 'Benchmark Category')
            ON CONFLICT (id) DO NOTHING
        """),
        {"cid": TEST_CATEGORY_ID},
    )
    await session.commit()



async def cleanup_test_adverts(session: AsyncSession) -> None:
    """Фаза Teardown: удаляем все тестовые объявления после прогона."""
    await session.execute(
        text("DELETE FROM adv_uuid.adverts WHERE id_seller = :sid"),
        {"sid": TEST_SELLER_ID},
    )
    await session.commit()


def make_sample_advert(idx: int) -> Advert:
    return Advert(
        id=uuid4(),
        content=f"Benchmark Advert #{idx}",
        description="Performance test description payload for SQL vs ORM comparison",
        id_category=TEST_CATEGORY_ID,
        price=1000 + idx,
        id_seller=TEST_PROFILE_ID,  # В create() репозиторий ищет seller.id по profile_id
    )


async def run_benchmark(impl: str, warmup_iters: int = 30, bench_iters: int = 200) -> None:
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:1234@localhost:5438/adverts_db",
    )
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    overhead_ns = measure_timer_overhead()
    print(f"[{impl.upper()}] Timer overhead (median): {overhead_ns:.1f} ns")

    results = []  # (scenario, iteration, duration_ns)

    async with session_factory() as session:
        await setup_test_entities(session)
        await cleanup_test_adverts(session)

        repo = (
            AdvertsRepository(session, AdvertsSqlBuilder())
            if impl == "sql"
            else OrmAdvertsRepository(session)
        )

        # 1. ФАЗА ПРОГРЕВА (WARMUP)
        print(f"[{impl.upper()}] Running warmup ({warmup_iters} iterations)...")
        warmup_ids = []
        for i in range(warmup_iters):
            created = await repo.create(make_sample_advert(i))
            if created:
                warmup_ids.append(created.id)
                await repo.get_by_id(created.id)

        for aid in warmup_ids:
            await repo.delete_advert(aid, TEST_SELLER_ID)

        # 2. СЦЕНАРИЙ WRITE-ONLY (Только запись)
        print(f"[{impl.upper()}] Measuring WRITE-ONLY ({bench_iters} iterations)...")
        created_ids = []
        total_write_start = time.perf_counter_ns()
        for i in range(bench_iters):
            adv = make_sample_advert(i)
            t0 = time.perf_counter_ns()
            created = await repo.create(adv)
            t1 = time.perf_counter_ns()
            results.append(("write_only", i + 1, t1 - t0))
            if created:
                created_ids.append(created.id)
        total_write_ms = (time.perf_counter_ns() - total_write_start) / 1_000_000

        # 3. СЦЕНАРИЙ READ-ONLY (Только чтение по заранее созданным ID)
        print(f"[{impl.upper()}] Measuring READ-ONLY ({bench_iters} iterations)...")
        total_read_start = time.perf_counter_ns()
        for i in range(bench_iters):
            target_id = created_ids[i % len(created_ids)]
            t0 = time.perf_counter_ns()
            await repo.get_by_id(target_id)
            t1 = time.perf_counter_ns()
            results.append(("read_only", i + 1, t1 - t0))
        total_read_ms = (time.perf_counter_ns() - total_read_start) / 1_000_000

        # 4. СЦЕНАРИЙ MIXED (Смешанный: создание + чтение + удаление)
        print(f"[{impl.upper()}] Measuring MIXED ({bench_iters} iterations)...")
        total_mixed_start = time.perf_counter_ns()
        for i in range(bench_iters):
            adv = make_sample_advert(10_000 + i)
            t0 = time.perf_counter_ns()
            created = await repo.create(adv)
            if created:
                await repo.get_by_id(created.id)
                await repo.delete_advert(created.id, TEST_SELLER_ID)
            t1 = time.perf_counter_ns()
            results.append(("mixed", i + 1, t1 - t0))
        total_mixed_ms = (time.perf_counter_ns() - total_mixed_start) / 1_000_000

        # 5. ФАЗА ЗАВЕРШЕНИЯ (TEARDOWN)
        await cleanup_test_adverts(session)

    await engine.dispose()

    # Сохраняем сырые результаты в CSV
    out_file = f"benchmark/results_{impl}.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["impl", "scenario", "iteration", "duration_ns", "duration_ms"])
        for scenario, idx, dur_ns in results:
            writer.writerow([impl, scenario, idx, dur_ns, f"{dur_ns / 1_000_000:.4f}"])

    print(f"\n[{impl.upper()}] Done! Saved to {out_file}")
    print(f"Summary -> Warmup ops: {warmup_iters * 3} | Bench ops per scenario: {bench_iters}")
    print(
        f"Total time -> Write: {total_write_ms:.2f} ms | "
        f"Read: {total_read_ms:.2f} ms | Mixed: {total_mixed_ms:.2f} ms"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--impl", choices=["sql", "orm"], required=True)
    args = parser.parse_args()
    asyncio.run(run_benchmark(args.impl))
