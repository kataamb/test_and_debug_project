import uuid
from typing import List
from abstract_repositories.ideal_repository import IDealRepository
from models.advert import Advert
from models.deal import Deal


class FakeDealRepository(IDealRepository):

    def __init__(self):
        self.deals: dict[uuid.UUID, Deal] = {}
        self.adverts_storage: dict[uuid.UUID, Advert] = {}

    async def create_deal(
        self, user_id: uuid.UUID, advert_id: uuid.UUID
    ) -> Deal:
        deal = Deal(
            id=uuid.uuid4(),
            id_advert=advert_id,
            id_customer=user_id,
            address="online",
        )
        self.deals[deal.id] = deal
        return deal

    async def get_deals_by_user(self, user_id: uuid.UUID) -> List[Advert]:
        advert_ids = [
            d.id_advert for d in self.deals.values() if d.id_customer == user_id
        ]
        return [
            ad for ad in self.adverts_storage.values() if ad.id in advert_ids
        ]

    async def is_in_deals(
        self, user_id: uuid.UUID, advert_id: uuid.UUID
    ) -> bool:
        return any(
            d.id_customer == user_id and d.id_advert == advert_id
            for d in self.deals.values()
        )

    async def is_bought(self, advert_id: uuid.UUID) -> bool:
        return any(d.id_advert == advert_id for d in self.deals.values())
