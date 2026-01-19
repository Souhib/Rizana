from typing import List

from fastapi import APIRouter, Depends, Query
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from rizana.api.controllers.wishlist import WishlistController
from rizana.api.models.table import User
from rizana.api.schemas.wishlist import WishCreate, WishResponse, WishUpdate
from rizana.dependencies import get_current_active_user, get_wishlist_controller

router = APIRouter(
    prefix="/wishlist",
    tags=["wishlist"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{wishlist_id}", response_model=WishResponse)
async def get_wishlist_item(
    wishlist_id: int,
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> WishResponse:
    """Get a wishlist item by ID.

    Args:
        wishlist_id: The ID of the wishlist item to retrieve.
        wishlist_controller: The wishlist controller.
        current_user: The current authenticated user.

    Returns:
        The wishlist item.
    """
    return await wishlist_controller.get_by_id(wishlist_id, current_user.id)


@router.get("/", response_model=List[WishResponse])
async def get_wishlist(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> List[WishResponse]:
    """Get wishlist items for the current user.

    Args:
        skip: Number of items to skip.
        limit: Maximum number of items to return.
        wishlist_controller: The wishlist controller.
        current_user: The current authenticated user.

    Returns:
        List of wishlist items.
    """
    return await wishlist_controller.get_by_user(current_user.id, skip, limit)


@router.post("/", response_model=WishResponse, status_code=HTTP_201_CREATED)
async def create_wishlist_item(
    wish_create: WishCreate,
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> WishResponse:
    """Create a new wishlist item.

    Args:
        wish_create: The wishlist item data.
        wishlist_controller: The wishlist controller.
        current_user: The current authenticated user.

    Returns:
        The created wishlist item.
    """
    return await wishlist_controller.create(wish_create, current_user.id)


@router.put("/{wishlist_id}", response_model=WishResponse)
async def update_wishlist_item(
    wishlist_id: int,
    wish_update: WishUpdate,
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> WishResponse:
    """Update a wishlist item.

    Args:
        wishlist_id: The ID of the wishlist item to update.
        wish_update: The updated wishlist item data.
        wishlist_controller: The wishlist controller.
        current_user: The current authenticated user.

    Returns:
        The updated wishlist item.
    """
    return await wishlist_controller.update(wishlist_id, wish_update, current_user.id)


@router.delete("/{wishlist_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    wishlist_id: int,
    wishlist_controller: WishlistController = Depends(get_wishlist_controller),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a wishlist item.

    Args:
        wishlist_id: The ID of the wishlist item to delete.
        wishlist_controller: The wishlist controller.
        current_user: The current authenticated user.
    """
    await wishlist_controller.delete(wishlist_id, current_user.id)
