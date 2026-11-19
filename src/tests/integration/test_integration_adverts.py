import uuid
import pytest
import allure
from sqlalchemy import text

from services.advert_service import AdvertService
from repositories.advert_repository import AdvertsRepository
from repositories.category_repository import CategoryRepository
from repositories.user_repository import UserRepository

from sql_builders.advert_sql_builder import AdvertsSqlBuilder
from sql_builders.category_sql_builder import CategorySqlBuilder
from sql_builders.user_sql_builder import UserSqlBuilder

from errors.error_services import (
    UserNotFound,
    AdvertNotFound,
    AdvertUserNotOwn,
)
from tests.test_data.models.mother_adverts import AdvertMother
from tests.test_data.models.mother_auth import UserMother
from tests.test_data.models.mother_category import CategoryMother


@allure.feature("Integration Tests")
@allure.story("AdvertService + PostgreSQL")
class TestAdvertServiceIntegration:
    """
    Интеграционные тесты: AdvertService + реальные репозитории + PostgreSQL.
    Использует только существующую фикстуру test_db_session.
    """

    @pytest.fixture
    async def advert_service(self, test_db_session):
        advert_repo = AdvertsRepository(test_db_session, AdvertsSqlBuilder())
        category_repo = CategoryRepository(test_db_session, CategorySqlBuilder())
        user_repo = UserRepository(test_db_session, UserSqlBuilder())
        return AdvertService(
            repo=advert_repo,
            repo_category=category_repo,
            repo_user=user_repo,
        )

    @pytest.fixture
    async def seeded_env(self, test_db_session):
        """Создает в БД уникального пользователя (profile + seller) и категорию."""
        suffix = uuid.uuid4().hex[:8]
        user = (
            UserMother.with_email(f"int_{suffix}@example.com")
            .model_copy(update={"nickname": f"int_user_{suffix}"})
        )
        category = CategoryMother.any_category().model_copy(
            update={"name": f"Категория_{suffix}"}
        )
        uid = str(user.id)

        await test_db_session.execute(
            text("""
                INSERT INTO adv_uuid.profiles (id, nickname, fio, email, phone_number, password)
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
        await test_db_session.execute(
            text("INSERT INTO adv_uuid.sellers (id, profile_id, rating) VALUES (:id, :pid, 0)"),
            {"id": uid, "pid": uid},
        )
        await test_db_session.execute(
            text("INSERT INTO adv_uuid.categories (id, name) VALUES (:id, :name)"),
            {"id": str(category.id), "name": category.name},
        )
        return user, category

    @allure.title("Интеграция: успешное создание и чтение объявления из БД")
    async def test_create_and_get_advert_integration(self, advert_service, seeded_env):
        # Arrange
        user, category = seeded_env
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=category.id
        )

        # Act
        created = await advert_service.create_advert(advert)
        fetched = await advert_service.get_advert(created.id)

        # Assert
        assert created is not None
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.content == advert.content
        assert fetched.id_category == category.id

    @allure.title("Интеграция: get_advert для несуществующего ID возвращает None")
    async def test_get_advert_missing_returns_none(self, advert_service):
        # Act
        fetched = await advert_service.get_advert(uuid.uuid4())

        # Assert
        assert fetched is None

    @allure.title("Интеграция: проверка авторства объявления (is_created)")
    async def test_is_created_integration(self, advert_service, seeded_env):
        # Arrange
        user, category = seeded_env
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=category.id
        )
        created = await advert_service.create_advert(advert)

        # Act & Assert
        assert await advert_service.is_created(user.id, created.id) is True

        with pytest.raises(AdvertNotFound):
            await advert_service.is_created(user.id, uuid.uuid4())

        with pytest.raises(UserNotFound):
            await advert_service.is_created(uuid.uuid4(), created.id)

    @allure.title("Интеграция: поиск по ключевому слову и категории через SQL-функцию БД")
    async def test_search_by_keyword_and_category_integration(self, advert_service, seeded_env):
        # Arrange
        user, category = seeded_env
        unique_word = f"Ноутбук_{uuid.uuid4().hex[:6]}"
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=category.id
        )
        advert.content = f"Продам {unique_word} недорого"
        created = await advert_service.create_advert(advert)

        # Act
        found = await advert_service.get_adverts_by_category_and_keyword(
            f"%{unique_word}%", category.id
        )

        # Assert
        assert len(found) == 1
        assert found[0].id == created.id

    @allure.title("Интеграция: получение объявлений по категории и общего списка")
    async def test_get_all_and_by_category_integration(self, advert_service, seeded_env):
        # Arrange
        user, category = seeded_env
        adv1 = AdvertMother.valid_advert_for_user_and_category(user.id, category.id)
        adv2 = AdvertMother.valid_advert_for_user_and_category(user.id, category.id)
        c1 = await advert_service.create_advert(adv1)
        c2 = await advert_service.create_advert(adv2)

        # Act
        by_cat = await advert_service.get_adverts_by_category(category.id)
        all_adv = await advert_service.get_all_adverts()

        # Assert
        assert {a.id for a in by_cat} == {c1.id, c2.id}
        all_ids = {a.id for a in all_adv}
        assert c1.id in all_ids and c2.id in all_ids

    @allure.title("Интеграция: получение объявлений конкретного пользователя")
    async def test_get_adverts_by_user_integration(self, advert_service, seeded_env):
        # Arrange
        user, category = seeded_env
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=category.id
        )
        created = await advert_service.create_advert(advert)

        # Act
        user_adverts = await advert_service.get_advert_by_user(user.id)

        # Assert
        assert any(a.id == created.id for a in user_adverts)



    @allure.title("Интеграция: успешное удаление объявления владельцем из БД")
    async def test_delete_own_advert_integration(self, advert_service, seeded_env):
        # Arrange
        user, category = seeded_env
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=category.id
        )
        created = await advert_service.create_advert(advert)

        # Act
        await advert_service.delete_advert(created.id, user.id)

        # Assert
        assert await advert_service.get_advert(created.id) is None

    @allure.title("Интеграция: удаление чужого объявления запрещено (AdvertUserNotOwn)")
    async def test_delete_foreign_advert_raises_error(self, advert_service, seeded_env, test_db_session):
        # Arrange
        owner, category = seeded_env
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=owner.id, category_id=category.id
        )
        created = await advert_service.create_advert(advert)

        stranger_id = uuid.uuid4()
        await test_db_session.execute(
            text("""
                INSERT INTO adv_uuid.profiles (id, nickname, fio, email, phone_number, password)
                VALUES (:id, :nick, 'Stranger User', :email, '+79990000000', '123')
            """),
            {
                "id": str(stranger_id),
                "nick": f"stranger_{stranger_id.hex[:6]}",
                "email": f"stranger_{stranger_id.hex[:6]}@example.com",
            },
        )

        # Act & Assert
        with pytest.raises(AdvertUserNotOwn):
            await advert_service.delete_advert(created.id, stranger_id)

        assert await advert_service.get_advert(created.id) is not None
