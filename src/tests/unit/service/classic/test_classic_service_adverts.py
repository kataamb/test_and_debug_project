"""
Классический стиль тестирования AdvertService.

В этом стиле мы используем фейковые репозитории (Fake*Repository), которые
хранят данные в памяти. Это позволяет проверить реальное взаимодействие
сервиса с репозиториями без базы данных.

Фейки наполняются тестовыми данными в Arrange-секции каждого теста.
Используются Object Mother (AdvertMother, UserMother, CategoryMother).
"""
import uuid

import pytest

from errors.error_services import AdvertNotFound, AdvertUserNotOwn, CategoryNotFound, UserNotFound
from api_v1.dto.advert_dto import AdvertUpdatePartialDTO
from tests.test_data.models.mother_adverts import AdvertMother
from tests.test_data.models.mother_category import CategoryMother
from tests.test_data.models.mother_auth import UserMother


# ==============================================================================
# Вспомогательные функции для наполнения фейковых репозиториев
# ==============================================================================

async def _add_category(fake_repo_category, category):
    """Добавляет категорию в фейковый репозиторий напрямую в хранилище."""
    fake_repo_category._storage[category.id] = category
    return category


async def _add_user(fake_repo_user, user):
    """Добавляет пользователя в фейковый репозиторий через его публичный метод."""
    await fake_repo_user.create(user)
    return user


async def _add_adverts(fake_repo_advert, adverts):
    """Добавляет объявления в фейковый репозиторий через его публичный метод."""
    for advert in adverts:
        await fake_repo_advert.create(advert)
    return adverts


# ==============================================================================
# Тесты для метода create_advert
# ==============================================================================
class TestCreateAdvertClassic:
    async def test_create_advert_when_category_not_found(self, service_advert_classic):
        # Arrange
        advert = AdvertMother.valid_advert()
        # Категорию в фейк НЕ добавляем

        # Act & Assert
        with pytest.raises(CategoryNotFound):
            await service_advert_classic.create_advert(advert)

        # Проверяем, что объявление не было создано
        all_adverts = await service_advert_classic.repo.get_all_adverts()
        assert all_adverts == []

    async def test_create_advert_when_category_exists(self, service_advert_classic):
        # Arrange
        category = CategoryMother.any_category()
        await _add_category(service_advert_classic.repo_category, category)
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=uuid.uuid4(), category_id=category.id
        )

        # Act
        result = await service_advert_classic.create_advert(advert)

        # Assert
        assert result is not None
        assert result.id == advert.id
        assert result.content == advert.content
        # Проверяем, что объявление действительно сохранилось в репозитории
        stored_advert = await service_advert_classic.repo.get_by_id(advert.id)
        assert stored_advert == advert


# ==============================================================================
# Тесты для метода get_advert
# ==============================================================================
class TestGetAdvertClassic:
    async def test_get_advert_when_not_found(self, service_advert_classic):
        # Arrange
        advert_id = uuid.uuid4()
        # Ничего не добавляем

        # Act
        result = await service_advert_classic.get_advert(advert_id)

        # Assert
        assert result is None

    async def test_get_advert_when_found(self, service_advert_classic):
        # Arrange
        advert = AdvertMother.valid_advert()
        await _add_adverts(service_advert_classic.repo, [advert])

        # Act
        result = await service_advert_classic.get_advert(advert.id)

        # Assert
        assert result == advert


# ==============================================================================
# Тесты для метода get_all_adverts
# ==============================================================================
class TestGetAllAdvertsClassic:
    async def test_get_all_adverts_when_empty(self, service_advert_classic):
        # Arrange
        # Ничего не добавляем

        # Act
        result = await service_advert_classic.get_all_adverts()

        # Assert
        assert result == []

    async def test_get_all_adverts_when_one(self, service_advert_classic):
        # Arrange
        adverts = AdvertMother.create_list(count=1)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_all_adverts()

        # Assert
        assert len(result) == 1
        assert result[0] == adverts[0]

    async def test_get_all_adverts_when_many(self, service_advert_classic):
        # Arrange
        adverts = AdvertMother.create_list(count=10)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_all_adverts()

        # Assert
        assert len(result) == 10
        # Проверяем, что все добавленные объявления присутствуют
        result_ids = {a.id for a in result}
        expected_ids = {a.id for a in adverts}
        assert result_ids == expected_ids


# ==============================================================================
# Тесты для метода get_advert_by_user
# ==============================================================================
class TestGetAdvertByUserClassic:
    async def test_get_advert_by_user_when_user_not_found(self, service_advert_classic):
        # Arrange
        user_id = uuid.uuid4()
        # Пользователя в фейк НЕ добавляем

        # Act & Assert
        with pytest.raises(UserNotFound):
            await service_advert_classic.get_advert_by_user(user_id)

    async def test_get_advert_by_user_when_user_has_no_adverts(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)

        # Act
        result = await service_advert_classic.get_advert_by_user(user.id)

        # Assert
        assert result == []

    async def test_get_advert_by_user_when_user_has_one_advert(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        adverts = AdvertMother.create_list_for_user(user_id=user.id, count=1)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_advert_by_user(user.id)

        # Assert
        assert len(result) == 1
        assert result[0].id_seller == user.id

    async def test_get_advert_by_user_when_user_has_many_adverts(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        adverts = AdvertMother.create_list_for_user(user_id=user.id, count=5)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_advert_by_user(user.id)

        # Assert
        assert len(result) == 5
        # Все объявления принадлежат пользователю
        assert all(a.id_seller == user.id for a in result)


# ==============================================================================
# Тесты для метода is_created
# ==============================================================================
class TestIsCreatedClassic:
    async def test_is_created_when_user_not_found(self, service_advert_classic):
        # Arrange
        user_id = uuid.uuid4()
        # Пользователя не добавляем
        advert = AdvertMother.valid_advert()
        await _add_adverts(service_advert_classic.repo, [advert])

        # Act & Assert
        with pytest.raises(UserNotFound):
            await service_advert_classic.is_created(user_id, advert.id)

    async def test_is_created_when_advert_not_found(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        advert_id = uuid.uuid4()
        # Объявление НЕ добавляем

        # Act & Assert
        with pytest.raises(AdvertNotFound):
            await service_advert_classic.is_created(user.id, advert_id)

    async def test_is_created_when_not_owner(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        # Создаем объявление другим пользователем
        other_user_id = uuid.uuid4()
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=other_user_id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])

        # Act
        result = await service_advert_classic.is_created(user.id, advert.id)

        # Assert
        assert result is False

    async def test_is_created_when_owner(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])

        # Act
        result = await service_advert_classic.is_created(user.id, advert.id)

        # Assert
        assert result is True


# ==============================================================================
# Тесты для метода get_adverts_by_key_word
# ==============================================================================
class TestGetAdvertsByKeyWordClassic:
    @pytest.mark.parametrize(
        "keyword, adverts_to_add, expected_count",
        [
            # 1) пустое ключевое слово (пустая строка), объявления есть в бд
            # В FakeAdvertRepository пустая строка содержится в любом content/description,
            # поэтому вернутся все объявления.
            ("", AdvertMother.create_list(count=5), 5),
            # 2) пустое ключевое слово, бд пустая
            ("", [], 0),
            # 3) ключевое слово содержит пробелы, объявления есть, и есть подходящие
            ("  test  ", AdvertMother.create_list_with_keyword("  test  ", count=5), 5),
            # 4) ключевое слово содержит пробелы, объявления есть, но не подходят
            # (все объявления с content "base test content" — подстрока "  test  " не входит)
            ("  test  ", AdvertMother.create_list(count=5), 0),
            # 5) ключевое слово содержит латиницу, подходящих нет
            # AdvertMother.create_list создает content "base test content",
            # который СОДЕРЖИТ "test". Чтобы не было совпадений, возьмем другое слово.
            ("qwerty", AdvertMother.create_list(count=5), 0),
            # 6) ключевое слово содержит латиницу, подходящие есть
            ("test", AdvertMother.create_list(count=5), 5),
        ],
    )
    async def test_get_adverts_by_key_word(
        self, service_advert_classic, keyword, adverts_to_add, expected_count
    ):
        # Arrange
        await _add_adverts(service_advert_classic.repo, adverts_to_add)

        # Act
        result = await service_advert_classic.get_adverts_by_key_word(keyword)

        # Assert
        assert len(result) == expected_count


# ==============================================================================
# Тесты для метода get_adverts_by_category
# ==============================================================================
class TestGetAdvertsByCategoryClassic:
    async def test_get_adverts_by_category_when_category_not_found(self, service_advert_classic):
        # Arrange
        category_id = uuid.uuid4()
        # Категорию не добавляем
        adverts = AdvertMother.create_list(count=5)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act & Assert
        with pytest.raises(CategoryNotFound):
            await service_advert_classic.get_adverts_by_category(category_id)

    async def test_get_adverts_by_category_when_category_exists_but_no_adverts(
        self, service_advert_classic
    ):
        # Arrange
        category = CategoryMother.any_category()
        await _add_category(service_advert_classic.repo_category, category)
        # Объявления с этой категорией не добавляем

        # Act
        result = await service_advert_classic.get_adverts_by_category(category.id)

        # Assert
        assert result == []

    async def test_get_adverts_by_category_when_category_exists_and_has_adverts(
        self, service_advert_classic
    ):
        # Arrange
        category = CategoryMother.any_category()
        await _add_category(service_advert_classic.repo_category, category)
        adverts = AdvertMother.create_list_for_category(category.id, count=5)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_adverts_by_category(category.id)

        # Assert
        assert len(result) == 5
        assert all(a.id_category == category.id for a in result)


# ==============================================================================
# Тесты для метода get_adverts_by_category_and_keyword
# ==============================================================================
class TestGetAdvertsByCategoryAndKeywordClassic:
    async def test_with_category_and_empty_keyword(self, service_advert_classic):
        # Arrange
        category = CategoryMother.any_category()
        await _add_category(service_advert_classic.repo_category, category)
        adverts = AdvertMother.create_list_for_category(category.id, count=5)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_adverts_by_category_and_keyword("", category.id)

        # Assert
        assert len(result) == 5
        assert all(a.id_category == category.id for a in result)

    async def test_with_non_existent_category(self, service_advert_classic):
        # Arrange
        category_id = uuid.uuid4()
        # Категорию не добавляем
        adverts = AdvertMother.create_list(count=5)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act & Assert
        with pytest.raises(CategoryNotFound):
            await service_advert_classic.get_adverts_by_category_and_keyword("", category_id)

    async def test_with_keyword_and_category_when_no_data(self, service_advert_classic):
        # Arrange
        keyword = "qwerty"
        category = CategoryMother.any_category()
        await _add_category(service_advert_classic.repo_category, category)
        # Создаем объявления в этой категории, но без ключевого слова
        adverts = AdvertMother.create_list_for_category(category.id, count=5)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_adverts_by_category_and_keyword(
            keyword, category.id
        )

        # Assert
        assert result == []

    async def test_with_keyword_and_category_when_data_exists(self, service_advert_classic):
        # Arrange
        keyword = "test"
        category = CategoryMother.any_category()
        await _add_category(service_advert_classic.repo_category, category)
        # AdvertMother.create_list_for_category создает content "base test content",
        # который содержит "test"
        adverts = AdvertMother.create_list_for_category(category.id, count=5)
        await _add_adverts(service_advert_classic.repo, adverts)

        # Act
        result = await service_advert_classic.get_adverts_by_category_and_keyword(
            keyword, category.id
        )

        # Assert
        assert len(result) == 5
        assert all(a.id_category == category.id for a in result)


# ==============================================================================
# Тесты для метода update_advert
# ==============================================================================
class TestUpdateAdvertClassic:
    async def test_update_when_user_not_found(self, service_advert_classic):
        # Arrange
        user_id = uuid.uuid4()
        advert_data = AdvertMother.valid_advert()
        # Пользователя не добавляем
        advert = AdvertMother.valid_advert()
        await _add_adverts(service_advert_classic.repo, [advert])

        # Act & Assert
        with pytest.raises(UserNotFound):
            await service_advert_classic.update_advert(user_id, advert.id, advert_data)

    async def test_update_when_advert_not_found(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        advert_id = uuid.uuid4()
        advert_data = AdvertMother.valid_advert()
        # Объявление не добавляем

        # Act & Assert
        with pytest.raises(AdvertNotFound):
            await service_advert_classic.update_advert(user.id, advert_id, advert_data)

    async def test_update_when_user_not_owner(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        # Объявление принадлежит другому пользователю
        other_user_id = uuid.uuid4()
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=other_user_id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])
        advert_data = AdvertMother.valid_advert()

        # Act & Assert
        with pytest.raises(AdvertUserNotOwn):
            await service_advert_classic.update_advert(user.id, advert.id, advert_data)

    async def test_update_success(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])

        new_advert_data = AdvertMother.with_id(advert.id)
        new_advert_data.id_seller = user.id

        # Act
        result = await service_advert_classic.update_advert(
            user.id, advert.id, new_advert_data
        )

        # Assert
        assert result.id == advert.id
        assert result.content == new_advert_data.content
        assert result.price == new_advert_data.price
        # Проверяем, что данные в репозитории обновились
        stored_advert = await service_advert_classic.repo.get_by_id(advert.id)
        assert stored_advert.content == new_advert_data.content


# ==============================================================================
# Тесты для метода partial_update_advert
# ==============================================================================
class TestPartialUpdateAdvertClassic:
    async def test_partial_update_when_user_not_owner(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        other_user_id = uuid.uuid4()
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=other_user_id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])
        update_data = AdvertUpdatePartialDTO(content="new content")

        # Act & Assert
        with pytest.raises(AdvertUserNotOwn):
            await service_advert_classic.partial_update_advert(
                user.id, advert.id, update_data
            )

    async def test_partial_update_success(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])

        new_content = "updated content"
        new_price = 999
        update_data = AdvertUpdatePartialDTO(content=new_content, price=new_price)

        # Act
        result = await service_advert_classic.partial_update_advert(
            user.id, advert.id, update_data
        )

        # Assert
        assert result.id == advert.id
        assert result.content == new_content
        assert result.price == new_price
        # Проверяем, что данные в репозитории обновились
        stored_advert = await service_advert_classic.repo.get_by_id(advert.id)
        assert stored_advert.content == new_content
        assert stored_advert.price == new_price


# ==============================================================================
# Тесты для метода delete_advert
# ==============================================================================
class TestDeleteAdvertClassic:

    async def test_delete_when_user_not_owner(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        other_user_id = uuid.uuid4()
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=other_user_id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])

        # Act & Assert
        with pytest.raises(AdvertUserNotOwn):
            await service_advert_classic.delete_advert(advert.id, user.id)

        # Проверяем, что объявление не было удалено
        assert await service_advert_classic.repo.get_by_id(advert.id) is not None

    async def test_delete_success(self, service_advert_classic):
        # Arrange
        user = UserMother.valid_user()
        await _add_user(service_advert_classic.repo_user, user)
        advert = AdvertMother.valid_advert_for_user_and_category(
            user_id=user.id, category_id=uuid.uuid4()
        )
        await _add_adverts(service_advert_classic.repo, [advert])

        # Act
        await service_advert_classic.delete_advert(advert.id, user.id)

        # Assert
        stored_advert = await service_advert_classic.repo.get_by_id(advert.id)
        assert stored_advert is None