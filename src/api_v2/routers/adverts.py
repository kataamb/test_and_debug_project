# api_v2/routers/adverts.py
from fastapi import APIRouter, Depends, status, HTTPException
from uuid import UUID

from api_v2.dependencies import get_service_locator
from core.create_jwt import get_current_user, get_optional_user


from service_locator import ServiceLocator
from api_v1.dto.advert_dto import (
    AdvertCreateDTO,
    AdvertUpdateFullDTO,
    AdvertUpdatePartialDTO,
    AdvertResponseDTO,
    AdvertListResponseDTO,
    AdvertSearchRequestDTO,
)
from errors.error_services import (
    AdvertNotFound,
    CategoryNotFound,
    UserNotFound,
    AdvertUserNotOwn,
)
from models.advert import Advert

api_v2_router_adverts = APIRouter(prefix="/adverts", tags=["Adverts v2"])


# ============== GET / ==============
@api_v2_router_adverts.get("/", response_model=AdvertListResponseDTO)
async def get_all_adverts(
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_optional_user)
):
    """Получить все объявления."""
    try:
        adverts = await locator.advert_service().get_all_adverts()
        items = []

        for advert in adverts:
            is_created = False
            is_liked = False
            is_bought_by_current = False

            if current_user:
                is_created = await locator.advert_service().is_created(current_user["id"], advert.id)
                is_liked = await locator.liked_service().is_liked(current_user["id"], advert.id)
                is_bought_by_current = await locator.deals_service().is_in_deals(current_user["id"], advert.id)

            dto = AdvertResponseDTO(
                id=advert.id,
                content=advert.content,
                description=advert.description,
                price=advert.price,
                id_category=advert.id_category,
                id_seller=advert.id_seller,
                date_created=advert.date_created,
                category_name=await locator.category_service().get_name_by_id(advert.id_category),
                seller_name='',
                is_created=is_created,
                is_liked=is_liked,
                is_bought=await locator.deals_service().is_bought(advert.id),
                is_bought_by_current=is_bought_by_current,
            )
            items.append(dto)

        return AdvertListResponseDTO(items=items)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve adverts: {str(e)}",
        )


# ============== POST / ==============
@api_v2_router_adverts.post("/", response_model=AdvertResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_advert(
        advert_data: AdvertCreateDTO,
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_current_user)
):
    """Создать новое объявление."""
    try:
        advert_obj = Advert(
            id=UUID(int=0),
            content=advert_data.content,
            description=advert_data.description,
            id_category=advert_data.id_category,
            price=advert_data.price,
            id_seller=current_user["id"],
        )
        print(advert_obj, current_user, 'aaaaa')

        advert = await locator.advert_service().create_advert(advert_obj)
        if advert is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create advert",
            )

        is_liked = await locator.liked_service().is_liked(current_user["id"], advert.id)
        is_bought_by_current = await locator.deals_service().is_in_deals(current_user["id"], advert.id)

        return AdvertResponseDTO(
            id=advert.id,
            content=advert.content,
            description=advert.description,
            price=advert.price,
            id_category=advert.id_category,
            id_seller=advert.id_seller,
            date_created=advert.date_created,
            category_name=await locator.category_service().get_name_by_id(advert.id_category),
            seller_name='',
            is_created=True,
            is_liked=is_liked,
            is_bought=await locator.deals_service().is_bought(advert.id),
            is_bought_by_current=is_bought_by_current,
        )
    except CategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create advert: {str(e)}",
        )



# ============== GET /created ==============
@api_v2_router_adverts.get("/created", response_model=AdvertListResponseDTO)
async def get_my_adverts(
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_current_user)
):
    """Получить объявления текущего пользователя."""
    try:
        adverts = await locator.advert_service().get_advert_by_user(current_user["id"])
        items = []

        for advert in adverts:
            is_liked = await locator.liked_service().is_liked(current_user["id"], advert.id)
            is_bought_by_current = await locator.deals_service().is_in_deals(current_user["id"], advert.id)

            dto = AdvertResponseDTO(
                id=advert.id,
                content=advert.content,
                description=advert.description,
                price=advert.price,
                id_category=advert.id_category,
                id_seller=advert.id_seller,
                date_created=advert.date_created,
                category_name=await locator.category_service().get_name_by_id(advert.id_category),
                seller_name='',
                is_created=True,
                is_liked=is_liked,
                is_bought=await locator.deals_service().is_bought(advert.id),
                is_bought_by_current=is_bought_by_current,
            )
            items.append(dto)

        return AdvertListResponseDTO(items=items)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve my adverts: {str(e)}",
        )


# ============== GET /liked ==============
@api_v2_router_adverts.get("/liked", response_model=AdvertListResponseDTO)
async def get_liked_adverts(
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_current_user)
):
    """Получить понравившиеся объявления."""
    try:
        adverts = await locator.liked_service().get_liked_by_user(current_user["id"])
        items = []

        for advert in adverts:
            dto = AdvertResponseDTO(
                id=advert.id,
                content=advert.content,
                description=advert.description,
                price=advert.price,
                id_category=advert.id_category,
                id_seller=advert.id_seller,
                date_created=advert.date_created,
                category_name=await locator.category_service().get_name_by_id(advert.id_category),
                seller_name='',
                is_created=False,
                is_liked=True,
                is_bought=await locator.deals_service().is_bought(advert.id),
                is_bought_by_current=await locator.deals_service().is_in_deals(current_user["id"], advert.id),
            )
            items.append(dto)

        return AdvertListResponseDTO(items=items)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve liked adverts: {str(e)}",
        )


# ============== GET /deals ==============
@api_v2_router_adverts.get("/deals", response_model=AdvertListResponseDTO)
async def get_deals_adverts(
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_current_user)
):
    """Получить объявления, купленные пользователем."""
    try:
        adverts = await locator.deals_service().get_deals_by_user(current_user["id"])
        items = []

        for advert in adverts:
            dto = AdvertResponseDTO(
                id=advert.id,
                content=advert.content,
                description=advert.description,
                price=advert.price,
                id_category=advert.id_category,
                id_seller=advert.id_seller,
                date_created=advert.date_created,
                category_name=await locator.category_service().get_name_by_id(advert.id_category),
                seller_name='',
                is_created=await locator.advert_service().is_created(current_user["id"], advert.id),
                is_liked=await locator.liked_service().is_liked(current_user["id"], advert.id),
                is_bought=True,
                is_bought_by_current=True,
            )
            items.append(dto)

        return AdvertListResponseDTO(items=items)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve deals adverts: {str(e)}",
        )





# ============== GET /{advert_id} ==============
@api_v2_router_adverts.get("/{advert_id}", response_model=AdvertResponseDTO)
async def get_advert(
        advert_id: UUID,
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_optional_user)
):
    """Получить объявление по ID."""
    try:
        advert = await locator.advert_service().get_advert(advert_id)
        if not advert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Advert with id={advert_id} not found",
            )

        is_created = False
        is_liked = False
        is_bought_by_current = False
        if current_user:
            is_created = await locator.advert_service().is_created(current_user["id"], advert.id)
            is_liked = await locator.liked_service().is_liked(current_user["id"], advert.id)
            is_bought_by_current = await locator.deals_service().is_in_deals(current_user["id"], advert.id)

        return AdvertResponseDTO(
            id=advert.id,
            content=advert.content,
            description=advert.description,
            price=advert.price,
            id_category=advert.id_category,
            id_seller=advert.id_seller,
            date_created=advert.date_created,
            category_name=await locator.category_service().get_name_by_id(advert.id_category),
            seller_name='',
            is_created=is_created,
            is_liked=is_liked,
            is_bought=await locator.deals_service().is_bought(advert.id),
            is_bought_by_current=is_bought_by_current,
        )
    except HTTPException:
        raise
    except AdvertNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve advert: {str(e)}",
        )


# ============== PUT /{advert_id} ==============
@api_v2_router_adverts.put("/{advert_id}", response_model=AdvertResponseDTO)
async def update_advert_full(
        advert_id: UUID,
        advert_data: AdvertUpdateFullDTO,
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_current_user)
):
    """Полное обновление объявления."""
    try:
        advert_obj = Advert(
            id=advert_id,
            content=advert_data.content,
            description=advert_data.description,
            id_category=advert_data.id_category,
            price=advert_data.price,
            id_seller=current_user["id"],
        )

        updated = await locator.advert_service().update_advert(
            current_user["id"], advert_id, advert_obj
        )

        return AdvertResponseDTO(
            id=updated.id,
            content=updated.content,
            description=updated.description,
            price=updated.price,
            id_category=updated.id_category,
            id_seller=updated.id_seller,
            date_created=updated.date_created,
            category_name=await locator.category_service().get_name_by_id(updated.id_category),
            seller_name='',
            is_created=True,
            is_liked=await locator.liked_service().is_liked(current_user["id"], updated.id),
            is_bought=await locator.deals_service().is_bought(updated.id),
            is_bought_by_current=await locator.deals_service().is_in_deals(current_user["id"], updated.id),
        )
    except AdvertNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except CategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except AdvertUserNotOwn as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update advert: {str(e)}",
        )


# ============== PATCH /{advert_id} ==============
@api_v2_router_adverts.patch("/{advert_id}", response_model=AdvertResponseDTO)
async def update_advert_partial(
        advert_id: UUID,
        advert_data: AdvertUpdatePartialDTO,
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_current_user)
):
    """Частичное обновление объявления."""
    try:
        updated = await locator.advert_service().partial_update_advert(
            current_user["id"], advert_id, advert_data
        )

        return AdvertResponseDTO(
            id=updated.id,
            content=updated.content,
            description=updated.description,
            price=updated.price,
            id_category=updated.id_category,
            id_seller=updated.id_seller,
            date_created=updated.date_created,
            category_name=await locator.category_service().get_name_by_id(updated.id_category),
            seller_name='',
            is_created=True,
            is_liked=await locator.liked_service().is_liked(current_user["id"], updated.id),
            is_bought=await locator.deals_service().is_bought(updated.id),
            is_bought_by_current=await locator.deals_service().is_in_deals(current_user["id"], updated.id),
        )
    except AdvertNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except CategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except AdvertUserNotOwn as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update advert: {str(e)}",
        )


# ============== DELETE /{advert_id} ==============
@api_v2_router_adverts.delete("/{advert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_advert(
        advert_id: UUID,
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_current_user)
):
    """Удалить объявление."""
    try:
        await locator.advert_service().delete_advert(advert_id, current_user["id"])
    except AdvertNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except AdvertUserNotOwn as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete advert: {str(e)}",
        )




# ============== POST /search ==============
@api_v2_router_adverts.post("/search", response_model=AdvertListResponseDTO)
async def search_adverts(
        search_data: AdvertSearchRequestDTO,
        locator: ServiceLocator = Depends(get_service_locator),
        current_user: dict = Depends(get_optional_user)
):
    """Поиск объявлений по ключевым словам и категории."""
    try:
        query = search_data.query or ''
        cat_id = search_data.id_category or UUID(int=0)

        adverts = await locator.advert_service().get_adverts_by_category_and_keyword(query, cat_id)
        items = []

        for advert in adverts:
            is_created = False
            is_liked = False
            is_bought_by_current = False

            if current_user:
                is_created = await locator.advert_service().is_created(current_user["id"], advert.id)
                is_liked = await locator.liked_service().is_liked(current_user["id"], advert.id)
                is_bought_by_current = await locator.deals_service().is_in_deals(current_user["id"], advert.id)

            dto = AdvertResponseDTO(
                id=advert.id,
                content=advert.content,
                description=advert.description,
                price=advert.price,
                id_category=advert.id_category,
                id_seller=advert.id_seller,
                date_created=advert.date_created,
                category_name=await locator.category_service().get_name_by_id(advert.id_category),
                seller_name='',
                is_created=is_created,
                is_liked=is_liked,
                is_bought=await locator.deals_service().is_bought(advert.id),
                is_bought_by_current=is_bought_by_current,
            )
            items.append(dto)

        return AdvertListResponseDTO(items=items)
    except CategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search adverts: {str(e)}",
        )