import uuid

import pytest
import allure

from errors.error_services import AdvertNotFound, AdvertUserNotOwn, CategoryNotFound, UserNotFound
from api_v1.dto.advert_dto import AdvertUpdatePartialDTO
from tests.test_data.models.mother_adverts import AdvertMother
from tests.test_data.models.mother_category import CategoryMother
from tests.test_data.models.mother_auth import UserMother


# ==============================================================================
# Тесты для метода create_advert
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("create_advert")
class TestCreateAdvert:
    @allure.title("create_advert: категория не найдена → CategoryNotFound")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_create_advert_when_category_not_found(
        self, service_advert_london, mock_repo_category, mock_repo_advert
    ):
        # Arrange
        with allure.step("Подготовить advert и мок: категории не существует"):
            advert = AdvertMother.valid_advert()
            mock_repo_category.get_name_by_id.return_value = None

        # Act & Assert
        with allure.step("Ожидать CategoryNotFound при создании"):
            with pytest.raises(CategoryNotFound):
                await service_advert_london.create_advert(advert)

        with allure.step("Проверить вызовы зависимостей"):
            mock_repo_category.get_name_by_id.assert_awaited_once_with(advert.id_category)
            mock_repo_advert.create.assert_not_awaited()

    @allure.title("create_advert: категория существует → advert создан")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_create_advert_when_category_exists(
        self, service_advert_london, mock_repo_category, mock_repo_advert
    ):
        # Arrange
        with allure.step("Подготовить категорию и advert, настроить моки"):
            category = CategoryMother.any_category()
            advert = AdvertMother.valid_advert_for_user_and_category(
                user_id=uuid.uuid4(), category_id=category.id
            )
            expected_advert = advert.model_copy(update={"id": uuid.uuid4()})
            mock_repo_category.get_name_by_id.return_value = category.name
            mock_repo_advert.create.return_value = expected_advert

        # Act
        with allure.step("Вызвать service.create_advert"):
            result = await service_advert_london.create_advert(advert)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == expected_advert
            mock_repo_category.get_name_by_id.assert_awaited_once_with(advert.id_category)
            mock_repo_advert.create.assert_awaited_once_with(advert)


# ==============================================================================
# Тесты для метода get_advert
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("get_advert")
class TestGetAdvert:
    @allure.title("get_advert: advert не найден → None")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_advert_when_not_found(self, service_advert_london, mock_repo_advert):
        # Arrange
        with allure.step("Настроить мок: репозиторий бросает ValueError"):
            advert_id = uuid.uuid4()
            mock_repo_advert.get_by_id.side_effect = ValueError("Not found")

        # Act
        with allure.step("Вызвать service.get_advert"):
            result = await service_advert_london.get_advert(advert_id)

        # Assert
        with allure.step("Проверить результат"):
            assert result is None
            mock_repo_advert.get_by_id.assert_awaited_once_with(advert_id)

    @allure.title("get_advert: advert найден")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_advert_when_found(self, service_advert_london, mock_repo_advert):
        # Arrange
        with allure.step("Настроить мок: репозиторий возвращает advert"):
            advert = AdvertMother.valid_advert()
            mock_repo_advert.get_by_id.return_value = advert

        # Act
        with allure.step("Вызвать service.get_advert"):
            result = await service_advert_london.get_advert(advert.id)

        # Assert
        with allure.step("Проверить результат"):
            assert result == advert
            mock_repo_advert.get_by_id.assert_awaited_once_with(advert.id)


# ==============================================================================
# Тесты для метода get_all_adverts
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("get_all_adverts")
class TestGetAllAdverts:
    @allure.title("get_all_adverts: пустой список")
    @allure.severity(allure.severity_level.MINOR)
    async def test_get_all_adverts_when_empty(self, service_advert_london, mock_repo_advert):
        # Arrange
        with allure.step("Настроить мок: пустой список"):
            mock_repo_advert.get_all_adverts.return_value = []

        # Act
        with allure.step("Вызвать service.get_all_adverts"):
            result = await service_advert_london.get_all_adverts()

        # Assert
        with allure.step("Проверить результат"):
            assert result == []
            mock_repo_advert.get_all_adverts.assert_awaited_once()

    @allure.title("get_all_adverts: одно объявление")
    @allure.severity(allure.severity_level.MINOR)
    async def test_get_all_adverts_when_one(self, service_advert_london, mock_repo_advert):
        # Arrange
        with allure.step("Настроить мок: список из 1 объявления"):
            adverts = AdvertMother.create_list(count=1)
            mock_repo_advert.get_all_adverts.return_value = adverts

        # Act
        with allure.step("Вызвать service.get_all_adverts"):
            result = await service_advert_london.get_all_adverts()

        # Assert
        with allure.step("Проверить результат"):
            assert result == adverts
            mock_repo_advert.get_all_adverts.assert_awaited_once()

    @allure.title("get_all_adverts: много объявлений")
    @allure.severity(allure.severity_level.MINOR)
    async def test_get_all_adverts_when_many(self, service_advert_london, mock_repo_advert):
        # Arrange
        with allure.step("Настроить мок: список из 10 объявлений"):
            adverts = AdvertMother.create_list(count=10)
            mock_repo_advert.get_all_adverts.return_value = adverts

        # Act
        with allure.step("Вызвать service.get_all_adverts"):
            result = await service_advert_london.get_all_adverts()

        # Assert
        with allure.step("Проверить результат"):
            assert result == adverts
            mock_repo_advert.get_all_adverts.assert_awaited_once()


# ==============================================================================
# Тесты для метода get_advert_by_user
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("get_advert_by_user")
class TestGetAdvertByUser:

    async def test_get_advert_by_user_when_user_has_no_adverts(
        self, service_advert_london, mock_repo_user, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить моки: пользователь есть, объявлений нет"):
            user = UserMother.valid_user()
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.get_advert_by_user.return_value = []

        # Act
        with allure.step("Вызвать service.get_advert_by_user"):
            result = await service_advert_london.get_advert_by_user(user.id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == []
            mock_repo_user.does_exist.assert_awaited_once_with(user.id)
            mock_repo_advert.get_advert_by_user.assert_awaited_once_with(user.id)

    @allure.title("get_advert_by_user: у пользователя одно объявление")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_advert_by_user_when_user_has_one_advert(
        self, service_advert_london, mock_repo_user, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить моки: у пользователя 1 объявление"):
            user = UserMother.valid_user()
            adverts = AdvertMother.create_list_for_user(user_id=user.id, count=1)
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.get_advert_by_user.return_value = adverts

        # Act
        with allure.step("Вызвать service.get_advert_by_user"):
            result = await service_advert_london.get_advert_by_user(user.id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == adverts
            mock_repo_user.does_exist.assert_awaited_once_with(user.id)
            mock_repo_advert.get_advert_by_user.assert_awaited_once_with(user.id)

    @allure.title("get_advert_by_user: у пользователя много объявлений")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_advert_by_user_when_user_has_many_adverts(
        self, service_advert_london, mock_repo_user, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить моки: у пользователя 5 объявлений"):
            user = UserMother.valid_user()
            adverts = AdvertMother.create_list_for_user(user_id=user.id, count=5)
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.get_advert_by_user.return_value = adverts

        # Act
        with allure.step("Вызвать service.get_advert_by_user"):
            result = await service_advert_london.get_advert_by_user(user.id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == adverts
            mock_repo_user.does_exist.assert_awaited_once_with(user.id)
            mock_repo_advert.get_advert_by_user.assert_awaited_once_with(user.id)


# ==============================================================================
# Тесты для метода is_created
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("is_created")
class TestIsCreated:
    @allure.title("is_created: пользователь не найден → UserNotFound")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_is_created_when_user_not_found(self, service_advert_london, mock_repo_user, mock_repo_advert):
        # Arrange
        with allure.step("Настроить мок: пользователь не существует"):
            user_id, advert_id = uuid.uuid4(), uuid.uuid4()
            mock_repo_user.does_exist.return_value = False

        # Act & Assert
        with allure.step("Ожидать UserNotFound"):
            with pytest.raises(UserNotFound):
                await service_advert_london.is_created(user_id, advert_id)

        with allure.step("Проверить вызовы зависимостей"):
            mock_repo_user.does_exist.assert_awaited_once_with(user_id)
            mock_repo_advert.advert_exists.assert_not_awaited()
            mock_repo_advert.is_created.assert_not_awaited()

    @allure.title("is_created: advert не найден → AdvertNotFound")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_is_created_when_advert_not_found(self, service_advert_london, mock_repo_user, mock_repo_advert):
        # Arrange
        with allure.step("Настроить моки: пользователь есть, advert отсутствует"):
            user_id, advert_id = uuid.uuid4(), uuid.uuid4()
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.advert_exists.return_value = False

        # Act & Assert
        with allure.step("Ожидать AdvertNotFound"):
            with pytest.raises(AdvertNotFound):
                await service_advert_london.is_created(user_id, advert_id)

        with allure.step("Проверить вызовы зависимостей"):
            mock_repo_user.does_exist.assert_awaited_once_with(user_id)
            mock_repo_advert.advert_exists.assert_awaited_once_with(advert_id)
            mock_repo_advert.is_created.assert_not_awaited()

    @allure.title("is_created: пользователь не владелец → False")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_is_created_when_not_owner(self, service_advert_london, mock_repo_user, mock_repo_advert):
        # Arrange
        with allure.step("Настроить моки: is_created возвращает False"):
            user_id, advert_id = uuid.uuid4(), uuid.uuid4()
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.advert_exists.return_value = True
            mock_repo_advert.is_created.return_value = False

        # Act
        with allure.step("Вызвать service.is_created"):
            result = await service_advert_london.is_created(user_id, advert_id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result is False
            mock_repo_user.does_exist.assert_awaited_once_with(user_id)
            mock_repo_advert.advert_exists.assert_awaited_once_with(advert_id)
            mock_repo_advert.is_created.assert_awaited_once_with(user_id, advert_id)

    @allure.title("is_created: пользователь владелец → True")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_is_created_when_owner(self, service_advert_london, mock_repo_user, mock_repo_advert):
        # Arrange
        with allure.step("Настроить моки: is_created возвращает True"):
            user_id, advert_id = uuid.uuid4(), uuid.uuid4()
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.advert_exists.return_value = True
            mock_repo_advert.is_created.return_value = True

        # Act
        with allure.step("Вызвать service.is_created"):
            result = await service_advert_london.is_created(user_id, advert_id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result is True
            mock_repo_user.does_exist.assert_awaited_once_with(user_id)
            mock_repo_advert.advert_exists.assert_awaited_once_with(advert_id)
            mock_repo_advert.is_created.assert_awaited_once_with(user_id, advert_id)


# ==============================================================================
# Тесты для метода get_adverts_by_key_word
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("get_adverts_by_key_word")
class TestGetAdvertsByKeyWord:
    @allure.title("get_adverts_by_key_word: параметризованный делегирующий тест")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "keyword, adverts_in_db, expected_result",
        [
            ("", AdvertMother.create_list(count=5), AdvertMother.create_list(count=5)),
            ("", [], []),
            ("  test  ", AdvertMother.create_list_with_keyword("  test  ", count=5), AdvertMother.create_list_with_keyword("  test  ", count=5)),
            ("  test  ", AdvertMother.create_list(count=5), []),
            ("test", AdvertMother.create_list(count=5), []),
            ("test", AdvertMother.create_list_with_keyword("test", count=5), AdvertMother.create_list_with_keyword("test", count=5)),
        ],
    )
    async def test_get_adverts_by_key_word(
        self, service_advert_london, mock_repo_advert, keyword, adverts_in_db, expected_result
    ):
        # Arrange
        with allure.step(f"Настроить мок: keyword={keyword!r}"):
            mock_repo_advert.get_adverts_by_key_word.return_value = expected_result

        # Act
        with allure.step("Вызвать service.get_adverts_by_key_word"):
            result = await service_advert_london.get_adverts_by_key_word(keyword)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == expected_result
            mock_repo_advert.get_adverts_by_key_word.assert_awaited_once_with(keyword)


# ==============================================================================
# Тесты для метода get_adverts_by_category
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("get_adverts_by_category")
class TestGetAdvertsByCategory:
    @allure.title("get_adverts_by_category: категория не найдена → CategoryNotFound")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_get_adverts_by_category_when_category_not_found(
        self, service_advert_london, mock_repo_category, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить мок: категории не существует"):
            category_id = uuid.uuid4()
            mock_repo_category.get_name_by_id.return_value = None

        # Act & Assert
        with allure.step("Ожидать CategoryNotFound"):
            with pytest.raises(CategoryNotFound):
                await service_advert_london.get_adverts_by_category(category_id)

        with allure.step("Проверить вызовы зависимостей"):
            mock_repo_category.get_name_by_id.assert_awaited_once_with(category_id)
            mock_repo_advert.get_adverts_by_category.assert_not_awaited()

    @allure.title("get_adverts_by_category: категория есть, объявлений нет")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_adverts_by_category_when_category_exists_but_no_adverts(
        self, service_advert_london, mock_repo_category, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить моки: категория есть, объявлений нет"):
            category = CategoryMother.any_category()
            mock_repo_category.get_name_by_id.return_value = category.name
            mock_repo_advert.get_adverts_by_category.return_value = []

        # Act
        with allure.step("Вызвать service.get_adverts_by_category"):
            result = await service_advert_london.get_adverts_by_category(category.id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == []
            mock_repo_category.get_name_by_id.assert_awaited_once_with(category.id)
            mock_repo_advert.get_adverts_by_category.assert_awaited_once_with(category.id)

    @allure.title("get_adverts_by_category: категория есть, есть объявления")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_adverts_by_category_when_category_exists_and_has_adverts(
        self, service_advert_london, mock_repo_category, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить моки: категория есть, 5 объявлений"):
            category = CategoryMother.any_category()
            adverts = AdvertMother.create_list_for_category(category.id, count=5)
            mock_repo_category.get_name_by_id.return_value = category.name
            mock_repo_advert.get_adverts_by_category.return_value = adverts

        # Act
        with allure.step("Вызвать service.get_adverts_by_category"):
            result = await service_advert_london.get_adverts_by_category(category.id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == adverts
            mock_repo_category.get_name_by_id.assert_awaited_once_with(category.id)
            mock_repo_advert.get_adverts_by_category.assert_awaited_once_with(category.id)


# ==============================================================================
# Тесты для метода get_adverts_by_category_and_keyword
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("get_adverts_by_category_and_keyword")
class TestGetAdvertsByCategoryAndKeyword:
    @allure.title("get_adverts_by_category_and_keyword: категория + пустое keyword")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_with_category_and_empty_keyword(
        self, service_advert_london, mock_repo_category, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить моки: категория есть, 5 объявлений"):
            category = CategoryMother.any_category()
            adverts = AdvertMother.create_list_for_category(category.id, count=5)
            mock_repo_category.get_name_by_id.return_value = category.name
            mock_repo_advert.get_adverts_by_category.return_value = adverts

        # Act
        with allure.step("Вызвать метод с пустым keyword"):
            result = await service_advert_london.get_adverts_by_category_and_keyword("", category.id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == adverts
            mock_repo_category.get_name_by_id.assert_awaited_once_with(category.id)
            mock_repo_advert.get_adverts_by_category.assert_awaited_once_with(category.id)

    @allure.title("get_adverts_by_category_and_keyword: несуществующая категория → CategoryNotFound")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_with_non_existent_category(
        self, service_advert_london, mock_repo_category
    ):
        # Arrange
        with allure.step("Настроить мок: категории не существует"):
            category_id = uuid.uuid4()
            mock_repo_category.get_name_by_id.return_value = None

        # Act & Assert
        with allure.step("Ожидать CategoryNotFound"):
            with pytest.raises(CategoryNotFound):
                await service_advert_london.get_adverts_by_category_and_keyword("", category_id)

        with allure.step("Проверить вызов зависимости"):
            mock_repo_category.get_name_by_id.assert_awaited_once_with(category_id)

    @allure.title("get_adverts_by_category_and_keyword: данных нет")
    @allure.severity(allure.severity_level.NORMAL)

    async def test_with_keyword_and_category_when_no_data(
        self, service_advert_london, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить мок: пустой результат"):
            keyword = "test"
            category_id = uuid.uuid4()
            mock_repo_advert.get_adverts_by_category_and_keyword.return_value = []

        # Act
        with allure.step("Вызвать метод"):
            result = await service_advert_london.get_adverts_by_category_and_keyword(keyword, category_id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == []
            mock_repo_advert.get_adverts_by_category_and_keyword.assert_awaited_once_with(keyword, category_id)

    @allure.title("get_adverts_by_category_and_keyword: данные есть")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_with_keyword_and_category_when_data_exists(self, service_advert_london, mock_repo_advert):
        # Arrange
        with allure.step("Настроить мок: 5 объявлений"):
            keyword = "test"
            category = CategoryMother.any_category()
            adverts = AdvertMother.create_list(count=5)
            mock_repo_advert.get_adverts_by_category_and_keyword.return_value = adverts

        # Act
        with allure.step("Вызвать метод"):
            result = await service_advert_london.get_adverts_by_category_and_keyword(keyword, category.id)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == adverts
            mock_repo_advert.get_adverts_by_category_and_keyword.assert_awaited_once_with(keyword, category.id)


# ==============================================================================
# Тесты для метода update_advert
# ==============================================================================

    async def test_update_success(self, service_advert_london, mock_repo_user, mock_repo_advert):
        # Arrange
        with allure.step("Настроить моки для успешного обновления"):
            user_id, advert_id = uuid.uuid4(), uuid.uuid4()
            advert_data = AdvertMother.valid_advert()
            updated_advert = AdvertMother.with_id(advert_id)
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.get_by_id.return_value = AdvertMother.with_id(advert_id)
            mock_repo_advert.is_created.return_value = True
            mock_repo_advert.update_advert.return_value = updated_advert

        # Act
        with allure.step("Вызвать service.update_advert"):
            result = await service_advert_london.update_advert(user_id, advert_id, advert_data)

        # Assert
        with allure.step("Проверить результат и вызовы"):
            assert result == updated_advert
            mock_repo_user.does_exist.assert_awaited_once_with(user_id)
            mock_repo_advert.get_by_id.assert_awaited_once_with(advert_id)
            mock_repo_advert.is_created.assert_awaited_once_with(user_id, advert_id)
            mock_repo_advert.update_advert.assert_awaited_once_with(advert_id, advert_data)


# ==============================================================================
# Тесты для метода partial_update_advert
# ==============================================================================
@allure.feature("Advert Service")
@allure.story("partial_update_advert")
class TestPartialUpdateAdvert:

    async def test_partial_update_when_user_not_owner(
        self, service_advert_london, mock_repo_user, mock_repo_advert
    ):
        # Arrange
        with allure.step("Настроить моки: is_created=False"):
            user_id, advert_id = uuid.uuid4(), uuid.uuid4()
            update_data = AdvertUpdatePartialDTO(content="new content")
            mock_repo_user.does_exist.return_value = True
            mock_repo_advert.get_by_id.return_value = AdvertMother.valid_advert()
            mock_repo_advert.is_created.return_value = False

        # Act & Assert
        with allure.step("Ожидать AdvertUserNotOwn"):
            with pytest.raises(AdvertUserNotOwn):
                await service_advert_london.partial_update_advert(user_id, advert_id, update_data)

        with allure.step("Проверить вызовы зависимостей"):
            mock_repo_user.does_exist.assert_awaited_once_with(user_id)
            mock_repo_advert.get_by_id.assert_awaited_once_with(advert_id)
            mock_repo_advert.is_created.assert_awaited_once_with(user_id, advert_id)
            mock_repo_advert.partial_update_advert.assert_not_awaited()

    @allure.title("partial_update_advert: успешное обновление")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_partial_update_success(self, service_advert_london, mock_repo_user, mock_repo_advert):
        # Arrange
        with allure.step("Настроить моки для успешного частичного обновления"):
            user_id, advert_id = uuid.uuid4(), uuid.uuid4