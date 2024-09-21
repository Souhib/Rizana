
from fastapi import APIRouter, Depends

from rizana.api.controllers.item import ItemController
from rizana.api.schemas.item import ItemCreate
from rizana.dependencies import get_item_controller

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def create_item(
    user: ItemCreate, item_controller: ItemController = Depends(get_item_controller)
):
    return await item_controller.create_item(user)
