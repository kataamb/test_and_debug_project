from abc import ABC, abstractmethod
from typing import List, Optional
from models.liked import Liked
from models.advert import Advert
from abstract_repositories.iliked_repository import ILikedRepository
from abstract_repositories.iadvert_repository import IAdvertRepository
from abstract_repositories.iuser_repository import IUserRepository
from uuid import UUID

from errors.error_services import CategoryNotFound, UserNotFound, AdvertNotFound, AdvertUserNotOwn



class ILikedService(ABC):
    @abstractmethod
    async def add_to_liked(self, user_id: UUID, advert_id :UUID) -> Optional[Liked]: ...

    @abstractmethod
    async def get_liked_by_user(self, user_id: UUID) -> List[Advert]: ...

    @abstractmethod
    async def remove_from_liked(self, user_id: UUID, advert_id: UUID) -> None: ...

    @abstractmethod
    async def is_liked(self, user_id: UUID, advert_id: UUID) -> bool: ...

class LikedService(ILikedService):
    def __init__(self, repo: ILikedRepository, repo_advert: IAdvertRepository,
                 repo_user: IUserRepository):
        self.repo = repo
        self.repo_advert = repo_advert
        self.repo_user = repo_user

    async def add_to_liked(self, user_id: UUID, advert_id: UUID) -> Optional[Liked]:
        if await self.repo.is_liked(user_id, advert_id):
            raise Exception(
                f"Advert {advert_id} already in liked for user {user_id}"
            )
        result = await self.repo.add_to_liked(user_id, advert_id)
        return result

    async def get_liked_by_user(self, user_id: UUID) -> List[Advert]:
        return await self.repo.get_liked_by_user(user_id)

    async def remove_from_liked(self, user_id: UUID, advert_id: UUID) -> None:
        return await self.repo.remove_from_liked(user_id, advert_id)

    async def is_liked(self, user_id: UUID, advert_id: UUID) -> bool:
        return await self.repo.is_liked(user_id, advert_id)






















