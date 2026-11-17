import uuid
from typing import List, Optional
from abstract_repositories.iliked_repository import ILikedRepository
from models.advert import Advert
from models.liked import Liked


class FakeLikedRepository(ILikedRepository):

    def __init__(self):
        self.likes: dict[uuid.UUID, Liked] = {}
        self.adverts_storage: dict[uuid.UUID, Advert] = {}

    async def add_to_liked(self, user_id: uuid.UUID, advert_id: uuid.UUID) -> Optional[Liked]:
        liked = Liked(id=uuid.uuid4(), id_customer=user_id, id_advert=advert_id)
        self.likes[liked.id] = liked
        return liked

    async def remove_from_liked(self, user_id: uuid.UUID, advert_id: uuid.UUID) -> None:
        target_id = None
        for item in self.likes.values():
            if item.id_customer == user_id and item.id_advert == advert_id:
                target_id = item.id
                break
        if target_id:
            del self.likes[target_id]

    async def get_liked_by_user(self, user_id: uuid.UUID) -> List[Advert]:
        advert_ids = [
            item.id_advert for item in self.likes.values() if item.id_customer == user_id
        ]
        return [
            ad for ad in self.adverts_storage.values() if ad.id in advert_ids
        ]

    async def is_liked(self, user_id: uuid.UUID, advert_id: uuid.UUID) -> bool:
        return any(
            item.id_customer == user_id and item.id_advert == advert_id
            for item in self.likes.values()
        )
