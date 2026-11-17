import uuid
from models.deal import Deal
from models.liked import Liked


class DealBuilder:

    def __init__(self):
        self.id = uuid.uuid4()
        self.id_advert = uuid.uuid4()
        self.id_customer = uuid.uuid4()
        self.address = "online"

    def with_ids(self, customer_id: uuid.UUID, advert_id: uuid.UUID):
        self.id_customer = customer_id
        self.id_advert = advert_id
        return self

    def build(self) -> Deal:
        return Deal(
            id=self.id,
            id_advert=self.id_advert,
            id_customer=self.id_customer,
            address=self.address,
        )


class LikedBuilder:

    def __init__(self):
        self.id = uuid.uuid4()
        self.id_advert = uuid.uuid4()
        self.id_customer = uuid.uuid4()

    def with_ids(self, customer_id: uuid.UUID, advert_id: uuid.UUID):
        self.id_customer = customer_id
        self.id_advert = advert_id
        return self

    def build(self) -> Liked:
        return Liked(
            id=self.id, id_advert=self.id_advert, id_customer=self.id_customer
        )
