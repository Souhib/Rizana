from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from rizana.api.controllers.item import ItemController
from rizana.api.models.table import User
from rizana.api.schemas.item import ItemCreate
from rizana.dependencies import get_current_active_user, get_item_controller

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=HTTP_201_CREATED)
async def create_item(
    item_create: ItemCreate,
    item_controller: ItemController = Depends(get_item_controller),
    current_user: User = Depends(get_current_active_user),
):
    return await item_controller.create_item(item_create, current_user.id)


@router.delete("/{item_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    item_controller: ItemController = Depends(get_item_controller),
    current_user: User = Depends(get_current_active_user),
):
    await item_controller.delete_item(item_id, current_user.id)


@router.get("/")
async def get_item(
    item_id: UUID,
    item_controller: ItemController = Depends(get_item_controller),
    current_user: User = Depends(get_current_active_user),
):
    return await item_controller.get_item(item_id, current_user.id)
