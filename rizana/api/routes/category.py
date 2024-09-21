
from fastapi import APIRouter, Depends

from rizana.api.controllers.item import ItemController
from rizana.api.models.table import User
from rizana.api.schemas.item import CategoryCreate
from rizana.dependencies import (
    get_current_active_admin_user,
    get_user_controller,
)

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def create_category(
    category_create: CategoryCreate,
    item_controller: ItemController = Depends(get_user_controller),
    current_user: User = Depends(get_current_active_admin_user),
):
    return await item_controller.create_category(category_create)


@router.delete("/{category_name}")
async def delete_category(
    category_name: str,
    item_controller: ItemController = Depends(get_user_controller),
    current_user: User = Depends(get_current_active_admin_user),
):
    return await item_controller.create_category(category_name)
