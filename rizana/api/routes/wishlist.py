from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from rizana.api.controllers.wishlist import WishlistController
from rizana.api.models.table import Item, User, Wish
from rizana.api.schemas.wishlist import WishCreate
from rizana.dependencies import (get_current_active_user,
                                 get_wishlist_controller)

router = APIRouter(
    prefix="/wishlist", tags=["wishlist"], responses={404: {"description": "Not found"}}
)


@router.post("/", status_code=HTTP_201_CREATED)
async def create_wish(
    wish_create: WishCreate,
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> Wish:
    return await wishlist_controller.create_wish(wish_create, current_user.id)


@router.delete("/{wish_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_wish(
    wish_id: UUID,
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> None:
    await wishlist_controller.remove_wish(wish_id, current_user.id)


@router.get("/")
async def get_wishlist(
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> list[Item]:
    return await wishlist_controller.get_wishlist(current_user.id)
