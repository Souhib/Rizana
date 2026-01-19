from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from rizana.api.controllers.payment import PaymentController
from rizana.api.models.stripe import PaymentIntentResponse
from rizana.api.models.table import PaymentMethod, User
from rizana.api.schemas.payment import PaymentMethodCreate
from rizana.dependencies import get_current_active_user, get_payment_controller

router = APIRouter(
    prefix="/payment-methods",
    tags=["payment-methods"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=HTTP_201_CREATED)
async def create_payment_method(
    payment_method_create: PaymentMethodCreate,
    payment_controller: PaymentController = Depends(get_payment_controller),
    current_user: User = Depends(get_current_active_user),
) -> PaymentMethod:
    return await payment_controller.create_payment(
        payment_method_create, current_user.id
    )


@router.delete("/{payment_method_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: UUID,
    payment_controller: PaymentController = Depends(get_payment_controller),
    current_user: User = Depends(get_current_active_user),
):
    await payment_controller.delete_payment_method(payment_method_id, current_user)


@router.get("/")
async def get_payment_method(
    payment_controller: PaymentController = Depends(get_payment_controller),
    current_user: User = Depends(get_current_active_user),
) -> list[PaymentMethod]:
    return await payment_controller.get_payments_method(current_user)


@router.post(
    "/create-payment-intent",
    status_code=HTTP_201_CREATED,
    response_model=PaymentIntentResponse,
)
async def create_payment_intent(
    order_id: UUID,
    payment_controller: PaymentController = Depends(get_payment_controller),
    current_user: User = Depends(get_current_active_user),
) -> PaymentIntentResponse:
    return await payment_controller.create_payment_intent(order_id, current_user)


@router.post(
    "/confirm-payment-intent/{payment_intent_id}", response_model=PaymentIntentResponse
)
async def confirm_payment_intent(
    payment_intent_id: str,
    payment_controller: PaymentController = Depends(get_payment_controller),
    current_user: User = Depends(get_current_active_user),
) -> PaymentIntentResponse:
    return await payment_controller.confirm_payment_intent(
        payment_intent_id, current_user
    )


router.mount("/static", StaticFiles(directory="static"), name="static")


@router.get("/test-payment")
async def get_payment_test_page():
    return FileResponse("static/payment.html")
