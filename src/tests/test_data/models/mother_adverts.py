import uuid
from typing import List
from tests.test_data.models.builder_adverts import AdvertBuilder
from models.advert import Advert

class AdvertMother:
    @staticmethod
    def valid_advert() -> Advert:
        return AdvertBuilder().build()

    @staticmethod
    def with_id(advert_id: uuid.UUID) -> Advert:
        return AdvertBuilder().with_id(advert_id).build()


    @staticmethod
    def create_list(count: int) -> List[Advert]:
        return [AdvertBuilder().build() for _ in range(count)]

    @staticmethod
    def create_list_for_user(user_id: uuid.UUID, count: int) -> List[Advert]:
        return [AdvertBuilder().with_seller_id(user_id).build() for _ in range(count)]

    @staticmethod
    def create_list_for_category(category_id: uuid.UUID, count: int) -> List[Advert]:
        return [AdvertBuilder().with_category_id(category_id).build() for _ in range(count)]

    @staticmethod
    def create_list_with_keyword(keyword: str, count: int) -> List[Advert]:
        return [
            AdvertBuilder().with_description(f"Товар с ключевым словом {keyword} и индексом {i}").build()
            for i in range(count)
        ]

    @staticmethod
    def valid_advert_for(user, category) -> Advert:
        """Advert с привязанными seller и category от переданных моделей"""
        return (
            AdvertBuilder()
            .with_seller_id(user.id)
            .with_category_id(category.id)
            .build()
        )

    @staticmethod
    def with_id_for(advert_id: uuid.UUID, user, category) -> Advert:
        return (
            AdvertBuilder()
            .with_id(advert_id)
            .with_seller_id(user.id)
            .with_category_id(category.id)
            .build()
        )

    @staticmethod
    def create_list_for(user, category, count: int) -> List[Advert]:
        return [
            AdvertBuilder()
            .with_seller_id(user.id)
            .with_category_id(category.id)
            .build()
            for _ in range(count)
        ]

    @staticmethod
    def valid_advert_for_user_and_category(user_id, category_id) -> Advert:
        return (
            AdvertBuilder()
            .with_seller_id(user_id)
            .with_category_id(category_id)
            .build()
        )