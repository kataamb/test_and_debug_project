import pytest
import allure
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from repositories.advert_repository import AdvertsRepository
from sql_builders.advert_sql_builder import AdvertsSqlBuilder

from tests.test_data.models.mother_auth import UserMother
from tests.test_data.models.mother_category import CategoryMother
from tests.test_data.models.mother_adverts import AdvertMother


@allure.feature("Advert Repository")
@allure.story("Unit tests")
class TestAdvertRepositoryUnit:
    """
    Unit тесты репозитория объявлений.

    Договорённость проекта:
        profiles.id == sellers.id == customers.id == user.id (один UUID).

    Следствия для тестов:
        * advert.id_seller == user.id  (а не отдельный seller_id).
        * repo.get_advert_by_user(user.id) возвращает advert'ы, где
          seller.profile_id == user.id, т.е. фактически advert.id_seller == user.id.
        * repo.delete_advert(advert_id, user.id) удаляет advert,
          потому что builder.delete делает WHERE id_seller = :user_id.
    """

    @pytest.fixture
    async def repo(self, test_db_session):
        with allure.step("Создать AdvertsRepository с AdvertsSqlBuilder"):
            return AdvertsRepository(
                session=test_db_session,
                builder=AdvertsSqlBuilder(),
            )

    @pytest.fixture
    async def seeded_user_category(self, test_db_session):
        """
        Готовит в БД профиль, seller'а и категорию.
        Все три записи используют ОДИН UUID (user.id).
        Возвращает (user, category).
        """
        with allure.step("Подготовить профиль, seller и категорию в БД"):
            user = UserMother.valid_user()
            category = CategoryMother.any_category()
            user_id_str = str(user.id)

            # profiles
            await test_db_session.execute(
                text("""
                    INSERT INTO adv_uuid.profiles
                        (id, nickname, fio, email, phone_number, password)
                    VALUES (:id, :nickname, :fio, :email, :phone_number, :password)
                """),
                {
                    "id": user_id_str,
                    "nickname": user.nickname,
                    "fio": user.fio,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "password": user.password,
                },
            )

            # sellers — тот же id, что и profiles.id
            await test_db_session.execute(
                text("""
                    INSERT INTO adv_uuid.sellers (id, profile_id, rating)
                    VALUES (:id, :profile_id, 0)
                """),
                {"id": user_id_str, "profile_id": user_id_str},
            )

            # categories
            await test_db_session.execute(
                text("INSERT INTO adv_uuid.categories (id, name) VALUES (:id, :name)"),
                {"id": str(category.id), "name": category.name},
            )

            return user, category

    @staticmethod
    async def _create_advert(repo, user, category, **overrides):
        """
        Создаёт advert, привязанный к user'у и категории.
        `user.id` совпадает с `sellers.id` по договорённости,
        поэтому билдер create найдёт seller'а по profile_id = user.id.
        """
        with allure.step("Создать advert для user и category"):
            advert = AdvertMother.valid_advert_for_user_and_category(
                user_id=user.id, category_id=category.id
            )
            for field, value in overrides.items():
                setattr(advert, field, value)
            return await repo.create(advert)

    # =========================================================================
    # 1. create() + get_by_id()
    # =========================================================================
    @allure.story("create()")
    @allure.title("Успешное создание advert")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_create_advert_success(self, repo, seeded_user_category):
        user, category = seeded_user_category
        with allure.step("Создать advert через репозиторий"):
            advert = AdvertMother.valid_advert_for_user_and_category(
                user_id=user.id, category_id=category.id
            )
            created = await repo.create(advert)

        with allure.step("Проверить результат"):
            assert created is not None
            assert created.content == advert.content

    @allure.story("get_by_id()")
    @allure.title("get_by_id возвращает созданный advert")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_get_by_id_returns_created_advert(self, repo, seeded_user_category):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        with allure.step(f"Получить advert по id={created.id}"):
            fetched = await repo.get_by_id(created.id)

        with allure.step("Проверить поля"):
            assert fetched.id == created.id
            assert fetched.content == created.content

    @allure.story("create()")
    @allure.title("Создание advert с отрицательной ценой → IntegrityError")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_create_advert_with_negative_price_raises_integrity_error(
        self, repo, seeded_user_category
    ):
        user, category = seeded_user_category
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=category.id
        )
        advert.price = -100

        with allure.step("Ожидать IntegrityError при создании"):
            with pytest.raises(IntegrityError):
                await repo.create(advert)

    @allure.story("get_by_id()")
    @allure.title("get_by_id для несуществующего id → ValueError")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_by_id_not_found_raises_value_error(self, repo):
        with allure.step("Запросить несуществующий advert"):
            with pytest.raises(ValueError, match="not found"):
                await repo.get_by_id(uuid4())

    # =========================================================================
    # 2. get_all_adverts()
    # =========================================================================
    @allure.story("get_all_adverts()")
    @allure.title("get_all_adverts возвращает созданный advert")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_all_adverts_returns_created(self, repo, seeded_user_category):
        user, category = seeded_user_category
        await self._create_advert(repo, user, category)

        with allure.step("Запросить все advert'ы"):
            result = await repo.get_all_adverts()

        with allure.step("Проверить, что созданный присутствует"):
            assert len(result) >= 1

    # =========================================================================
    # 3. get_advert_by_user()
    # =========================================================================
    @allure.story("get_advert_by_user()")
    @allure.title("get_advert_by_user возвращает только advert'ы пользователя")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_get_advert_by_user_returns_only_his_adverts(
        self, repo, seeded_user_category
    ):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        with allure.step(f"Запросить advert'ы пользователя {user.id}"):
            user_adverts = await repo.get_advert_by_user(user.id)

        with allure.step("Проверить выборку"):
            assert len(user_adverts) == 1
            assert user_adverts[0].id == created.id
            assert user_adverts[0].id_seller == user.id  # один UUID на всё

    # =========================================================================
    # 4. is_created()
    # =========================================================================
    @allure.story("is_created()")
    @allure.title("is_created → True для владельца")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_is_created_returns_true_for_owner(self, repo, seeded_user_category):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        with allure.step("Проверить is_created для владельца"):
            result = await repo.is_created(user.id, created.id)

        assert result is True

    @allure.story("is_created()")
    @allure.title("is_created → False для чужого пользователя")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_is_created_returns_false_for_stranger(
        self, repo, seeded_user_category
    ):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        with allure.step("Проверить is_created для постороннего uuid"):
            result = await repo.is_created(uuid4(), created.id)

        assert result is False

    # =========================================================================
    # 5. Фильтрация
    # =========================================================================
    @allure.story("Фильтрация")
    @allure.title("Поиск по ключевому слову находит advert")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_adverts_by_keyword(self, repo, seeded_user_category):
        user, category = seeded_user_category
        created = await self._create_advert(
            repo, user, category, content="Уникальный Игровой Ноутбук"
        )

        with allure.step("Искать advert'ы по ключевому слову 'Игровой'"):
            result = await repo.get_adverts_by_key_word("Игровой")

        with allure.step("Проверить результат"):
            assert len(result) == 1
            assert result[0].id == created.id

    @allure.story("Фильтрация")
    @allure.title("Фильтр по категории находит advert")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_adverts_by_category(self, repo, seeded_user_category):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        with allure.step(f"Искать advert'ы по категории {category.id}"):
            result = await repo.get_adverts_by_category(category.id)

        with allure.step("Проверить результат"):
            assert len(result) == 1
            assert result[0].id == created.id

    @allure.story("Фильтрация")
    @allure.title("Фильтр по дате включает созданный advert")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_adverts_by_date_filter_includes_created(
        self, repo, seeded_user_category
    ):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        now = datetime.now()
        with allure.step("Запросить advert'ы за последние сутки"):
            result = await repo.get_adverts_by_filter(
                now - timedelta(days=1), now + timedelta(days=1)
            )

        with allure.step("Проверить результат"):
            # Assert
            result_ids = {adv.id for adv in result}
            assert created.id in result_ids

    # =========================================================================
    # 6. update_advert()
    # =========================================================================
    @allure.story("update_advert()")
    @allure.title("update_advert меняет content и price")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_update_advert_changes_content_and_price(
        self, repo, seeded_user_category
    ):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        created.content = "Полностью Новое Имя"
        created.price = 9999

        with allure.step("Выполнить полное обновление advert"):
            updated = await repo.update_advert(created.id, created)

        with allure.step("Проверить изменения"):
            assert updated.content == "Полностью Новое Имя"
            assert updated.price == 9999

    @allure.story("update_advert()")
    @allure.title("update_advert для несуществующего id → ValueError")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_update_advert_not_found_raises_value_error(self, repo):
        with allure.step("Обновить несуществующий advert"):
            with pytest.raises(ValueError, match="not found"):
                await repo.update_advert(uuid4(), AdvertMother.valid_advert())

    # =========================================================================
    # 7. partial_update_advert()
    # =========================================================================
    @allure.story("partial_update_advert()")
    @allure.title("partial_update_advert меняет только price")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_partial_update_advert_changes_only_price(
        self, repo, seeded_user_category
    ):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)
        original_content = created.content

        with allure.step("Частично обновить только price"):
            updated = await repo.partial_update_advert(created.id, {"price": 12345})

        with allure.step("Проверить, что content не изменился"):
            assert updated.price == 12345
            assert updated.content == original_content

    @allure.story("partial_update_advert()")
    @allure.title("partial_update_advert для несуществующего id → ValueError")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_partial_update_advert_not_found_raises_value_error(self, repo):
        with allure.step("Частично обновить несуществующий advert"):
            with pytest.raises(ValueError, match="not found"):
                await repo.partial_update_advert(uuid4(), {"price": 100})

    # =========================================================================
    # 8. delete_advert()
    # =========================================================================
    @allure.story("delete_advert()")
    @allure.title("delete_advert удаляет advert из БД")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_delete_advert_removes_it_from_db(self, repo, seeded_user_category):
        user, category = seeded_user_category
        created = await self._create_advert(repo, user, category)

        with allure.step("Удалить advert владельцем"):
            await repo.delete_advert(created.id, user.id)

        with allure.step("Проверить, что advert больше не найден"):
            with pytest.raises(ValueError, match="not found"):
                await repo.get_by_id(created.id)