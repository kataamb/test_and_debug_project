"""
Unit (интеграционные с БД) тесты репозитория сделок.

Договорённость проекта:
    profiles.id == customers.id == sellers.id == user.id.
    То есть id_customer в deals == user_id (тот же UUID).

Следствия:
    * Чтобы создать deal, нужны: profile + customer с тем же id,
      категория + seller + advert (advert привязан к seller).
    * repo.get_deals_by_user(user.id) вернёт advert'ы,
      у которых в deals.id_customer записан customer с profile_id == user.id.
"""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from repositories.deal_repository import DealRepository
from repositories.advert_repository import AdvertsRepository
from sql_builders.deal_sql_builder import DealSqlBuilder
from sql_builders.advert_sql_builder import AdvertsSqlBuilder

from tests.test_data.models.mother_auth import UserMother
from tests.test_data.models.mother_category import CategoryMother
from tests.test_data.models.mother_adverts import AdvertMother


class TestDealRepositoryUnit:

    @pytest.fixture
    async def repo(self, test_db_session):
        return DealRepository(
            session=test_db_session,
            builder=DealSqlBuilder(),
        )

    @pytest.fixture
    async def advert_repo(self, test_db_session):
        return AdvertsRepository(
            session=test_db_session,
            builder=AdvertsSqlBuilder(),
        )

    # ------------------------------------------------------------------
    # Вспомогательная функция: создаёт пользователя (profile + customer + seller)
    # с одним и тем же UUID и возвращает объект User.
    # ------------------------------------------------------------------
    @staticmethod
    async def _seed_user(session, user):
        uid = str(user.id)
        await session.execute(
            text("""
                INSERT INTO adv_uuid.profiles
                    (id, nickname, fio, email, phone_number, password)
                VALUES (:id, :nickname, :fio, :email, :phone_number, :password)
            """),
            {
                "id": uid,
                "nickname": user.nickname,
                "fio": user.fio,
                "email": user.email,
                "phone_number": user.phone_number,
                "password": user.password,
            },
        )
        await session.execute(
            text("""
                INSERT INTO adv_uuid.customers (id, profile_id, rating)
                VALUES (:id, :profile_id, 0)
            """),
            {"id": uid, "profile_id": uid},
        )
        await session.execute(
            text("""
                INSERT INTO adv_uuid.sellers (id, profile_id, rating)
                VALUES (:id, :profile_id, 0)
            """),
            {"id": uid, "profile_id": uid},
        )
        return user

    @staticmethod
    async def _seed_category(session, category):
        await session.execute(
            text("INSERT INTO adv_uuid.categories (id, name) VALUES (:id, :name)"),
            {"id": str(category.id), "name": category.name},
        )
        return category

    # ------------------------------------------------------------------
    # Композитная фикстура: user + category + advert (от этого user'а).
    # ------------------------------------------------------------------
    @pytest.fixture
    async def seeded_user_category_advert(self, test_db_session, advert_repo):
        user = UserMother.valid_user()
        category = CategoryMother.any_category()

        await self._seed_user(test_db_session, user)
        await self._seed_category(test_db_session, category)

        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=category.id
        )
        advert = await advert_repo.create(advert)

        return user, category, advert

    # ------------------------------------------------------------------
    # Фикстура второго пользователя (для тестов изоляции) + его advert.
    # ------------------------------------------------------------------
    @pytest.fixture
    async def seeded_second_user_advert(
        self, test_db_session, advert_repo, seeded_user_category_advert
    ):
        _, category, _ = seeded_user_category_advert
        other_user = UserMother.valid_user()
        await self._seed_user(test_db_session, other_user)

        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=other_user.id, category_id=category.id
        )
        advert = await advert_repo.create(advert)
        return other_user, advert

    # =====================================================================
    # 1. create_deal()
    # =====================================================================


    async def test_create_deal_when_customer_not_found_raises_sqlalchemy_error(
        self, repo, seeded_user_category_advert
    ):
        _, _, advert = seeded_user_category_advert
        stranger_id = uuid.uuid4()  # в customers такого нет

        with pytest.raises(SQLAlchemyError):
            await repo.create_deal(stranger_id, advert.id)


    async def test_get_deals_by_user_when_no_deals_returns_empty(
        self, repo, seeded_user_category_advert
    ):
        user, _, _ = seeded_user_category_advert

        result = await repo.get_deals_by_user(user.id)

        assert result == []

    # 2.2 У пользователя ровно одна сделка → список из 1 нужного advert.
    async def test_get_deals_by_user_when_one_deal(
        self, repo, seeded_user_category_advert
    ):
        user, _, advert = seeded_user_category_advert
        await repo.create_deal(user.id, advert.id)

        result = await repo.get_deals_by_user(user.id)

        assert len(result) == 1
        assert result[0].id == advert.id

    # 2.3 У пользователя 5 сделок → список из 5, все с нужными id_advert.
    async def test_get_deals_by_user_when_many_deals(
        self, repo, advert_repo, test_db_session, seeded_user_category_advert
    ):
        user, category, _ = seeded_user_category_advert

        # Создаём 5 объявлений и 5 сделок
        expected_advert_ids = set()
        for _ in range(5):
            a = AdvertMother.valid_advert_for_user_and_category(
                user_id=user.id, category_id=category.id
            )
            a = await advert_repo.create(a)
            await repo.create_deal(user.id, a.id)
            expected_advert_ids.add(a.id)

        result = await repo.get_deals_by_user(user.id)

        assert len(result) == 5
        assert {a.id for a in result} == expected_advert_ids


    # 3.1 Пользователь купил это объявление → True.
    async def test_is_in_deals_returns_true_for_buyer(
        self, repo, seeded_user_category_advert
    ):
        user, _, advert = seeded_user_category_advert
        await repo.create_deal(user.id, advert.id)

        assert await repo.is_in_deals(user.id, advert.id) is True



    # 3.3 Объявления не существует → False.
    async def test_is_in_deals_returns_false_when_advert_does_not_exist(
        self, repo, seeded_user_category_advert
    ):
        user, _, _ = seeded_user_category_advert
        nonexistent_advert_id = uuid.uuid4()

        assert await repo.is_in_deals(user.id, nonexistent_advert_id) is False


    # 4.1 Объявление куплено (кем угодно) → True.
    async def test_is_bought_returns_true_when_deal_exists(
        self, repo, seeded_user_category_advert
    ):
        user, _, advert = seeded_user_category_advert
        await repo.create_deal(user.id, advert.id)

        assert await repo.is_bought(advert.id) is True

    # 4.2 Объявление не куплено → False.
    async def test_is_bought_returns_false_when_no_deals(
        self, repo, seeded_user_category_advert
    ):
        _, _, advert = seeded_user_category_advert
        # Сделку не создаём

        assert await repo.is_bought(advert.id) is False

    # 4.3 Объявления не существует → False.
    async def test_is_bought_returns_false_when_advert_does_not_exist(self, repo):
        nonexistent_advert_id = uuid.uuid4()

        assert await repo.is_bought(nonexistent_advert_id) is False