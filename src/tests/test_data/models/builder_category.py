import uuid
from models.category import Category


class CategoryBuilder:

    def __init__(self):
        self.id = uuid.uuid4()
        self.name = "Тестовая категория Транспорт"

    def with_id(self, category_id: uuid.UUID):
        self.id = category_id
        return self

    def with_name(self, name: str):
        self.name = name
        return self

    def build(self) -> Category:
        return Category(id=self.id, name=self.name)
