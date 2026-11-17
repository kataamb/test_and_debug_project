import uuid
from typing import List
from abstract_repositories.icategory_repository import ICategoryRepository
from models.category import Category

class FakeCategoryRepository(ICategoryRepository):
    def __init__(self):
        self._storage: dict[uuid.UUID, Category] = {}

    async def get_all(self) -> List[Category]:
        return List(self._storage.values())

    async def get_name_by_id(self, id_category: uuid.UUID) -> str:
        for category_id in self._storage:
            if category_id == id_category:
                return self._storage[category_id].name
        else:
            return ""

