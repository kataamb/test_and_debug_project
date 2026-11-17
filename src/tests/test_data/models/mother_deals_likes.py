import uuid
from typing import List
from tests.test_data.models.builder_deals_likes import DealBuilder, LikedBuilder
from models.deal import Deal
from models.liked import Liked


class DealMother:

    @staticmethod
    def valid_deal_for(customer_id: uuid.UUID, advert_id: uuid.UUID) -> Deal:
        return DealBuilder().with_ids(customer_id, advert_id).build()

    @staticmethod
    def create_list(count: int) -> List[Deal]:
        return [DealBuilder().build() for _ in range(count)]


class LikedMother:

    @staticmethod
    def valid_liked_for(customer_id: uuid.UUID, advert_id: uuid.UUID) -> Liked:
        return LikedBuilder().with_ids(customer_id, advert_id).build()

    @staticmethod
    def create_list(count: int) -> List[Liked]:
        return [LikedBuilder().build() for _ in range(count)]
