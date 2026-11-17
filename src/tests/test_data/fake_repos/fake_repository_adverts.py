


import uuid
from typing import List, Optional
from datetime import datetime, timezone
from abstract_repositories.iadvert_repository import IAdvertRepository
from models.advert import Advert


class FakeAdvertRepository(IAdvertRepository):
    def __init__(self):
        # Внутреннее хранилище: id (UUID) -> Advert
        self._storage: dict[uuid.UUID, Advert] = {}

    async def create(self, advert: Advert) -> Optional[Advert]:
        # Если ID пустой (UUID по умолчанию), генерируем новый, как это делает Postgres
        if advert.id == uuid.UUID(int=0) or advert.id is None:
            advert.id = uuid.uuid4()

        # Задаем дату создания, если её нет
        if not advert.date_created:
            advert.date_created = datetime.now(timezone.utc)

        self._storage[advert.id] = advert
        return advert

    async def get_by_id(self, advert_id: uuid.UUID) -> Optional[Advert]:
        return self._storage.get(advert_id)

    async def get_all_adverts(self) -> List[Advert]:
        # Сортируем по дате создания (убывание), как в твоем SQL-билдере
        return sorted(
            list(self._storage.values()),
            key=lambda x: x.date_created or datetime.min,
            reverse=True
        )

    async def get_advert_by_user(self, user_id: uuid.UUID) -> List[Advert]:
        return sorted(
            [ad for ad in self._storage.values() if ad.id_seller == user_id],
            key=lambda x: x.date_created or datetime.min,
            reverse=True
        )

    async def is_created(self, user_id: uuid.UUID, advert_id: uuid.UUID) -> bool:
        advert = self._storage.get(advert_id)
        return advert is not None and advert.id_seller == user_id

    async def get_adverts_by_key_word(self, key_word: str) -> List[Advert]:
        kw = key_word.lower()
        return [
            ad for ad in self._storage.values()
            if kw in ad.content.lower() or kw in ad.description.lower()
        ]

    async def get_adverts_by_filter(self, begin_time: datetime, end_time: datetime) -> List[Advert]:
        return [
            ad for ad in self._storage.values()
            if ad.date_created and begin_time <= ad.date_created <= end_time
        ]

    async def get_adverts_by_category(self, category_id: uuid.UUID) -> List[Advert]:
        return [ad for ad in self._storage.values() if ad.id_category == category_id]

    async def get_adverts_by_category_and_keyword(self, keyword: str, category_id: uuid.UUID) -> List[Advert]:
        kw = keyword.lower()
        return [
            ad for ad in self._storage.values()
            if ad.id_category == category_id and (kw in ad.content.lower() or kw in ad.description.lower())
        ]

    async def update_advert(self, advert_id: uuid.UUID, advert: Advert) -> Advert:
        if advert_id not in self._storage:
            raise ValueError(f"Advert with id {advert_id} not found")
        self._storage[advert_id] = advert
        return advert

    async def partial_update_advert(self, advert_id: uuid.UUID, update_data: dict) -> Advert:
        if advert_id not in self._storage:
            raise ValueError(f"Advert with id {advert_id} not found")

        advert = self._storage[advert_id]
        advert_dict = advert.model_dump()

        advert_dict.update(update_data)

        updated_advert = Advert(**advert_dict)
        self._storage[advert_id] = updated_advert
        return updated_advert

    async def delete_advert(self, advert_id: uuid.UUID, user_id: uuid.UUID) -> None:
        if advert_id in self._storage:
            del self._storage[advert_id]

    async def advert_exists(self, advert_id: uuid.UUID) -> bool:
        if advert_id in self._storage:
            return True
        else:
            return False