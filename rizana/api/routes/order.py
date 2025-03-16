from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from rizana.api.controllers.order import OrderController
from rizana.api.models.table import Order, User
from rizana.api.schemas.order import OrderCreate
from rizana.dependencies import get_current_active_user, get_user_controller

router = APIRouter(
    prefix="/order",
    tags=["order"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=HTTP_201_CREATED)
async def create_order(
    order_create: OrderCreate,
    order_controller: OrderController = Depends(get_user_controller),
    current_user: User = Depends(get_current_active_user),
) -> Order:
    return await order_controller.create_order(order_create, current_user)
