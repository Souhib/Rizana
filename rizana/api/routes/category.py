from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from rizana.api.controllers.item import ItemController
from rizana.api.models.table import User
from rizana.api.schemas.item import CategoryCreate
from rizana.dependencies import (get_current_active_admin_user,
                                 get_item_controller)

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{category_name}")
async def get_category(
    category_name: str,
    item_controller: ItemController = Depends(get_item_controller),
    current_user: User = Depends(get_current_active_admin_user),
):
    return await item_controller.get_category(category_name)


@router.post("/", status_code=HTTP_201_CREATED)
async def create_category(
    category_create: CategoryCreate,
    item_controller: ItemController = Depends(get_item_controller),
    current_user: User = Depends(get_current_active_admin_user),
):
    return await item_controller.create_category(category_create)


@router.delete("/{category_name}", status_code=HTTP_204_NO_CONTENT)
async def delete_category(
    category_name: str,
    item_controller: ItemController = Depends(get_item_controller),
    current_user: User = Depends(get_current_active_admin_user),
):
    return await item_controller.delete_category(category_name)
