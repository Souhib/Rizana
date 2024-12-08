from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from rizana.api.controllers.payment import PaymentController
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


@router.post("/create-payment-intent", status_code=HTTP_201_CREATED)
async def create_payment_intent(
    payment_intent_create: PaymentIntentCreate,
    current_user: User = Depends(get_current_active_user),
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=payment_intent_create.amount,
            currency=payment_intent_create.currency,
            metadata={"user_id": str(current_user.id)},
        )
        return {"client_secret": intent.client_secret}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
