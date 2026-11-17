import uuid
from datetime import datetime, timezone
from models.advert import Advert  

class AdvertBuilder:
    def __init__(self):
        self.id = uuid.uuid4()
        self.content = "base test content"
        self.description = "base test description"
        self.id_category = uuid.uuid4()
        self.price = 500  
        self.id_seller = uuid.uuid4()
        self.date_created = datetime.now(timezone.utc)

 
    def with_id(self, advert_id: uuid.UUID):
        self.id = advert_id
        return self

    def with_price(self, price: int):
        self.price = price
        return self

    def with_description(self, description: str):
        self.description = description
        return self

    def with_seller_id(self, seller_id: uuid.UUID):
        self.id_seller = seller_id
        return self

    def with_category_id(self, category_id: uuid.UUID):
        self.id_category = category_id
        return self

    def build(self) -> Advert:
        return Advert(
            id=self.id,
            content=self.content,
            description=self.description,
            id_category=self.id_category,
            price=self.price,
            id_seller=self.id_seller,
            date_created=self.date_created
        )
