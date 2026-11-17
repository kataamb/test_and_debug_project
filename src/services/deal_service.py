from abc import ABC, abstractmethod
from typing import List
from models.deal import Deal
from models.advert import Advert
from abstract_repositories.ideal_repository import IDealRepository
from abstract_repositories.iadvert_repository import IAdvertRepository
from abstract_repositories.iuser_repository import IUserRepository
from uuid import UUID

from errors.error_services import DealDoubleBuying, UserNotFound, AdvertNotFound, DealAlreadyBought


class IDealsService(ABC):
    @abstractmethod
    async def create_deal(self, user_id: UUID, advert_id :UUID) -> Deal: ...

    @abstractmethod
    async def get_deals_by_user(self, user_id: UUID) -> List[Advert]: ...

    @abstractmethod
    async def is_in_deals(self, user_id: UUID, advert_id: UUID) -> bool: ...

    @abstractmethod
    async def is_bought(self, advert_id: UUID) -> bool: ...

class DealsService(IDealsService):
    def __init__(self, repo: IDealRepository, repo_advert: IAdvertRepository,
                 repo_user: IUserRepository):
        self.repo = repo
        self.repo_advert = repo_advert
        self.repo_user = repo_user

    async def create_deal(self, user_id: UUID, advert_id :UUID) -> Deal:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)
        does_exist_advert = await self.repo_advert.advert_exists(advert_id)
        if not does_exist_advert:
            raise AdvertNotFound

        already_bought = await self.repo.is_bought(advert_id)
        if already_bought:

            raise DealAlreadyBought

        if await self.repo.is_in_deals(user_id, advert_id):
            raise DealDoubleBuying()
        result = await self.repo.create_deal(user_id, advert_id)
        return result

    async def get_deals_by_user(self, user_id: UUID) -> List[Advert]:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)
        return await self.repo.get_deals_by_user(user_id)

    async def is_in_deals(self, user_id: UUID, advert_id: UUID) -> bool:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)
        does_exist_advert = await self.repo_advert.advert_exists(advert_id)
        if not does_exist_advert:
            raise AdvertNotFound(advert_id)

        return await self.repo.is_in_deals(user_id, advert_id)


    async def is_bought(self, advert_id: UUID) -> bool:
        does_exist_advert = await self.repo_advert.advert_exists(advert_id)
        if not does_exist_advert:
            raise AdvertNotFound(advert_id)
        return await self.repo.is_bought(advert_id)





















