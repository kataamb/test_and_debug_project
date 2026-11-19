import os
import uuid
import pytest
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

APP_URL = os.getenv("APP_URL", "http://localhost:8001")
TEST_DB_URL = os.getenv(
    "TEST_DB_URL",
    "postgresql+asyncpg://postgres:1234@localhost:5438/adverts_db",
)


@pytest.mark.asyncio
async def test_e2e_user_adverts_lifecycle():
    unique_id = uuid.uuid4().hex[:8]
    category_id = uuid.uuid4()
    bg_seller_id = uuid.uuid4()
    bg_advert_ids = [uuid.uuid4(), uuid.uuid4()]

    user_email = f"e2e_{unique_id}@example.com"
    user_password = "SecurePassword123!"
    user_username = f"user_{unique_id}"
    created_user_id = None

    engine = create_async_engine(TEST_DB_URL, future=True)

    # 0. Наполнение витрины: категория, продавец и 2 объявления
    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO adv_uuid.categories (id, name) VALUES (:id, :name)"),
            {"id": str(category_id), "name": f"E2E_Cat_{unique_id}"},
        )
        await conn.execute(
            text("""
                INSERT INTO adv_uuid.profiles (id, nickname, fio, email, phone_number, password)
                VALUES (:id, :nick, :fio, :email, :phone, :pwd)
            """),
            {
                "id": str(bg_seller_id),
                "nick": f"seed_seller_{unique_id}",
                "fio": "Тестовый Продавец Витрины",
                "email": f"seed_{unique_id}@example.com",
                "phone": "+79990001122",
                "pwd": "seed_password",
            },
        )
        await conn.execute(
            text("INSERT INTO adv_uuid.sellers (id, profile_id, rating) VALUES (:id, :pid, 5)"),
            {"id": str(bg_seller_id), "pid": str(bg_seller_id)},
        )
        for idx, adv_id in enumerate(bg_advert_ids, start=1):
            await conn.execute(
                text("""
                    INSERT INTO adv_uuid.adverts (id, content, description, price, id_category, id_seller)
                    VALUES (:id, :content, :desc, :price, :cat_id, :seller_id)
                """),
                {
                    "id": str(adv_id),
                    "content": f"Витринный товар №{idx}",
                    "desc": "Тестовое наполнение витрины",
                    "price": 10000 * idx,
                    "cat_id": str(category_id),
                    "seller_id": str(bg_seller_id),
                },
            )

    try:
        async with httpx.AsyncClient(base_url=APP_URL, timeout=15.0) as client:
            # 1. Регистрация нового пользователя
            reg_resp = await client.post(
                "/api/v1/users/register",
                json={
                    "id": str(uuid.uuid4()),
                    "username": user_username,
                    "email": user_email,
                    "full_name": f"E2E User {unique_id}",
                    "phone": "+79991234567",
                    "password": user_password,
                    "rep_password": user_password,
                },
            )
            assert reg_resp.status_code == 201, f"Ошибка регистрации: {reg_resp.text}"
            created_user_id = reg_resp.json()["id"]

            # 2. Логин и получение JWT
            login_resp = await client.post(
                "/api/v1/users/login",
                json={"email": user_email, "password": user_password},
            )
            assert login_resp.status_code == 200, f"Ошибка логина: {login_resp.text}"
            token = login_resp.json()["access_token"]
            assert token
            auth_headers = {"Authorization": f"Bearer {token}"}

            # 3. Просмотр всех объявлений на витрине
            all_resp = await client.get("/api/v2/adverts/", headers=auth_headers)
            assert all_resp.status_code == 200, f"Ошибка получения ленты: {all_resp.text}"
            all_ids = {item["id"] for item in all_resp.json()["items"]}
            assert {str(i) for i in bg_advert_ids}.issubset(all_ids)

            # 4. Создание первого объявления
            first_resp = await client.post(
                "/api/v2/adverts/",
                headers=auth_headers,
                json={
                    "content": "Первое объявление: Наушники",
                    "description": "Беспроводные наушники",
                    "price": 5500,
                    "id_category": str(category_id),
                },
            )
            assert first_resp.status_code == 201, f"Ошибка создания 1-го объявления: {first_resp.text}"
            first_advert_id = first_resp.json()["id"]

            # 5. Создание второго объявления
            second_resp = await client.post(
                "/api/v2/adverts/",
                headers=auth_headers,
                json={
                    "content": "Второе объявление: Монитор",
                    "description": "IPS матрица 144 Гц",
                    "price": 24000,
                    "id_category": str(category_id),
                },
            )
            assert second_resp.status_code == 201, f"Ошибка создания 2-го объявления: {second_resp.text}"
            second_advert_id = second_resp.json()["id"]

            # 6. Получение списка своих объявлений (ожидаем 2)
            my_resp = await client.get("/api/v2/adverts/created", headers=auth_headers)
            assert my_resp.status_code == 200, f"Ошибка чтения своих объявлений: {my_resp.text}"
            my_items = my_resp.json()["items"]
            my_ids = [item["id"] for item in my_items]
            assert len(my_items) == 2
            assert first_advert_id in my_ids
            assert second_advert_id in my_ids

            # 7. Удаление первого объявления
            del_resp = await client.delete(
                f"/api/v2/adverts/{first_advert_id}",
                headers=auth_headers,
            )
            assert del_resp.status_code == 204, f"Ошибка удаления 1-го объявления: {del_resp.text}"

    finally:
        # Очистка тестовых данных из БД
        async with engine.begin() as conn:
            if created_user_id:
                await conn.execute(
                    text("DELETE FROM adv_uuid.profiles WHERE id = :uid"),
                    {"uid": str(created_user_id)},
                )
            await conn.execute(
                text("DELETE FROM adv_uuid.profiles WHERE id = :sid"),
                {"sid": str(bg_seller_id)},
            )
            await conn.execute(
                text("DELETE FROM adv_uuid.categories WHERE id = :cid"),
                {"cid": str(category_id)},
            )
        await engine.dispose()
