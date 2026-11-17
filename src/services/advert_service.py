from abc import ABC, abstractmethod
from typing import List, Optional
from models.advert import Advert
from api_v1.dto.advert_dto import AdvertUpdatePartialDTO
from abstract_repositories.iadvert_repository import IAdvertRepository
from abstract_repositories.icategory_repository import ICategoryRepository
from abstract_repositories.iuser_repository import IUserRepository
from uuid import UUID


from errors.error_services import CategoryNotFound, UserNotFound, AdvertNotFound, AdvertUserNotOwn

class IAdvertService(ABC):
    @abstractmethod
    async def create_advert(self, advert: Advert) -> Optional[Advert]: ...

    @abstractmethod
    async def get_advert(self, advert_id: UUID) -> Optional[Advert]: ...

    @abstractmethod
    async def get_all_adverts(self) -> List[Advert]: ...

    @abstractmethod
    async def get_advert_by_user(self, user_id: UUID) -> List[Advert]: ...

    @abstractmethod
    async def is_created(self, user_id: UUID, advert_id: UUID) -> bool: ...

    @abstractmethod
    async def get_adverts_by_key_word(self, key_word: str) -> List[Advert]: ...

    @abstractmethod
    async def get_adverts_by_category(self, category_id: UUID) -> List[Advert]: ...

    @abstractmethod
    async def get_adverts_by_category_and_keyword(self, keyword: str, category_id: UUID) -> List[Advert]: ...

    @abstractmethod
    async def update_advert(self, user_id: UUID, advert_id: UUID, advert_data: Advert) -> Advert: ...

    @abstractmethod
    async def partial_update_advert(self, user_id: UUID, advert_id: UUID, advert_data: AdvertUpdatePartialDTO) -> Advert: ...

    @abstractmethod
    async def delete_advert(self, advert_id: UUID, user_id: UUID) -> None: ...



class AdvertService(IAdvertService):
    def __init__(self, repo: IAdvertRepository,
                 repo_category:ICategoryRepository,
                 repo_user: IUserRepository):
        self.repo = repo
        self.repo_category = repo_category
        self.repo_user = repo_user


    async def create_advert(self, advert: Advert) -> Optional[Advert]:
        id_category = await self.repo_category.get_name_by_id(advert.id_category)
        if not id_category:
            raise CategoryNotFound(advert.id_category)
        result = await self.repo.create(advert)
        return result

    async def get_advert(self, advert_id: UUID) -> Optional[Advert]:
        try:
            return await self.repo.get_by_id(advert_id)
        except ValueError:
            return None

    async def get_all_adverts(self) -> List[Advert]:
        return await self.repo.get_all_adverts()

    async def get_advert_by_user(self, user_id: UUID) -> List[Advert]:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)
        return await self.repo.get_advert_by_user(user_id)

    async def is_created(self, user_id: UUID, advert_id: UUID) -> bool:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)
        does_exist_advert = await self.repo.advert_exists(advert_id)
        if not does_exist_advert:
            raise AdvertNotFound
        return await self.repo.is_created(user_id, advert_id)

    async def get_adverts_by_key_word(self, key_word: str) -> List[Advert]:
        return await self.repo.get_adverts_by_key_word(key_word)


    async def get_adverts_by_category(self, category_id: UUID) -> List[Advert]:
        id_category = await self.repo_category.get_name_by_id(category_id)
        if not id_category:
            raise CategoryNotFound(category_id)
        return await self.repo.get_adverts_by_category(category_id)

    async def get_adverts_by_category_and_keyword(self, keyword: str, category_id: UUID) -> List[Advert]:
        if not keyword and not category_id:
            return await self.repo.get_all_adverts()

        elif keyword and not category_id:
            return await self.repo.get_adverts_by_key_word(keyword)

        elif not keyword and category_id:
            id_category = await self.repo_category.get_name_by_id(category_id)
            if not id_category:
                raise CategoryNotFound(category_id)
            return await self.repo.get_adverts_by_category(category_id)

        else:
            id_category = await self.repo_category.get_name_by_id(category_id)
            if not id_category:
                raise CategoryNotFound(category_id)
            return await self.repo.get_adverts_by_category_and_keyword(keyword, category_id)

    async def update_advert(self, user_id: UUID, advert_id: UUID, advert_data: Advert) -> Advert:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)

        existing_advert = await self.repo.get_by_id(advert_id)
        if not existing_advert:
            raise AdvertNotFound

        is_created_by_curr = await self.repo.is_created(user_id, advert_id)
        if not is_created_by_curr:
            raise AdvertUserNotOwn

        return await self.repo.update_advert(advert_id, advert_data)

    async def partial_update_advert(self, user_id: UUID, advert_id: UUID, advert_data: AdvertUpdatePartialDTO) -> Advert:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)

        existing_advert = await self.repo.get_by_id(advert_id)
        if not existing_advert:
            raise AdvertNotFound

        is_created_by_curr = await self.repo.is_created(user_id, advert_id)
        if not is_created_by_curr:
            raise AdvertUserNotOwn
		    
        # Подготавливаем данные для обновления
        update_dict = {}
        if advert_data.content is not None:
            update_dict["content"] = advert_data.content

        if advert_data.description is not None:
            update_dict["description"] = advert_data.description

        if advert_data.price is not None:
            update_dict["price"] = str(advert_data.price)

        if advert_data.id_category is not None:
            id_category = await self.repo_category.get_name_by_id(advert_data.id_category)
            if not id_category:
                raise CategoryNotFound(advert_data.id_category)

            update_dict["id_category"] = str(advert_data.id_category)

        return await self.repo.partial_update_advert(advert_id, update_dict)


    async def delete_advert(self, advert_id: UUID, user_id: UUID) -> None:
        does_exist_user = await self.repo_user.does_exist(user_id)
        if not does_exist_user:
            raise UserNotFound(user_id)

        existing_advert = await self.repo.get_by_id(advert_id)
        if not existing_advert:
            raise AdvertNotFound

        is_created_by_curr = await self.repo.is_created(user_id, advert_id)
        if not is_created_by_curr:
            raise AdvertUserNotOwn

        await self.repo.delete_advert(advert_id, user_id)

