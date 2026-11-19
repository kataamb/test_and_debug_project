from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, delete, select, text, update
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from abstract_repositories.iadvert_repository import IAdvertRepository
from models.advert import Advert


class BenchBase(DeclarativeBase):
    pass


class AdvertORM(BenchBase):
    __tablename__ = "adverts"
    __table_args__ = {"schema": "adv_uuid"}

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    content: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    id_category: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    price: Mapped[int] = mapped_column(Integer)
    id_seller: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    date_created: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=datetime.utcnow,
    )



class SellerORM(BenchBase):
    __tablename__ = "sellers"
    __table_args__ = {"schema": "adv_uuid"}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))


class OrmAdvertsRepository(IAdvertRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, advert: Advert) -> Optional[Advert]:
        try:
            stmt = select(SellerORM.id).where(SellerORM.profile_id == advert.id_seller)
            seller_id = (await self.session.execute(stmt)).scalar_one_or_none()
            if not seller_id:
                return None

            orm_obj = AdvertORM(
                content=advert.content,
                description=advert.description,
                id_category=advert.id_category,
                price=advert.price,
                id_seller=seller_id,
            )
            self.session.add(orm_obj)
            await self.session.commit()
            await self.session.refresh(orm_obj)
            return Advert.model_validate(orm_obj, from_attributes=True)
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, advert_id: UUID) -> Optional[Advert]:
        try:
            stmt = select(AdvertORM).where(AdvertORM.id == advert_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()
            if not orm_obj:
                raise ValueError(f"Advert with id {advert_id} not found")
            return Advert.model_validate(orm_obj, from_attributes=True)
        except SQLAlchemyError:
            raise

    async def get_all_adverts(self) -> List[Advert]:
        try:
            stmt = select(AdvertORM).order_by(AdvertORM.date_created.desc())
            result = await self.session.execute(stmt)
            return [Advert.model_validate(obj, from_attributes=True) for obj in result.scalars().all()]
        except SQLAlchemyError:
            raise

    async def update_advert(self, advert_id: UUID, advert: Advert) -> Advert:
        try:
            stmt = (
                update(AdvertORM)
                .where(AdvertORM.id == advert_id)
                .values(
                    content=advert.content,
                    description=advert.description,
                    id_category=advert.id_category,
                    price=advert.price,
                )
                .returning(AdvertORM)
            )
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()
            if not orm_obj:
                raise ValueError(f"Advert with id {advert_id} not found")
            await self.session.commit()
            return Advert.model_validate(orm_obj, from_attributes=True)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_advert(self, advert_id: UUID, user_id: UUID) -> None:
        try:
            stmt = delete(AdvertORM).where(
                AdvertORM.id == advert_id,
                AdvertORM.id_seller == user_id,
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def advert_exists(self, advert_id: UUID) -> bool:
        try:
            stmt = select(AdvertORM.id).where(AdvertORM.id == advert_id).limit(1)
            result = await self.session.execute(stmt)
            return result.first() is not None
        except SQLAlchemyError:
            return False

    # Заглушки для остальных методов IAdvertRepository, не участвующих в бенчмарке
    async def get_advert_by_user(self, user_id: UUID) -> List[Advert]:
        raise NotImplementedError

    async def is_created(self, user_id: UUID, advert_id: UUID) -> bool:
        raise NotImplementedError

    async def get_adverts_by_key_word(self, key_word: str) -> List[Advert]:
        raise NotImplementedError

    async def get_adverts_by_filter(self, begin_time: datetime, end_time: datetime) -> List[Advert]:
        raise NotImplementedError

    async def get_adverts_by_category(self, category_id: UUID) -> List[Advert]:
        raise NotImplementedError

    async def get_adverts_by_category_and_keyword(self, keyword: str, category_id: UUID) -> List[Advert]:
        raise NotImplementedError

    async def partial_update_advert(self, advert_id: UUID, update_data: dict) -> Advert:
        raise NotImplementedError
