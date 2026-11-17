from tests.test_data.models.builder_category import CategoryBuilder
from models.category import Category


class CategoryMother:

    @staticmethod
    def any_category() -> Category:
        """Возвращает любую готовую валидную категорию"""
        return CategoryBuilder().build()
