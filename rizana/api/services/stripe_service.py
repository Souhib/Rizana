from datetime import datetime

import stripe

from rizana.api.models.stripe import PaymentIntentResponse
from rizana.api.models.table import Order, User
from rizana.api.schemas.error import (
    InvalidPaymentAmountError,
    PaymentIntentConfirmationError,
    PaymentIntentCreationError,
    PaymentMethodRequiredError,
    PayoutError,
    UserNotAllowed,
)


class StripeService:

    def __init__(
        self, stripe_api_key: str, frontend_success_url: str, frontend_cancel_url: str
    ):
        self._set_stripe_api_key(stripe_api_key)
        self.success_url = frontend_success_url
        self.cancel_url = frontend_cancel_url

    def _set_stripe_api_key(self, stripe_api_key: str) -> None:
        """
        Sets the Stripe API key for the service.

        Args:
            stripe_api_key (str): The Stripe API key to be set.
        """
        stripe.api_key = stripe_api_key

    @staticmethod
    async def create_payment_intent(
        order: Order, current_user: User
    ) -> PaymentIntentResponse:
        """
        Creates a Stripe payment intent for an order.

        This method creates a new payment intent in Stripe with the order details and metadata.
        The payment intent is used to process the payment for the order.

        Args:
            order (Order): The order object containing payment details including total price,
                          currency, and associated IDs (payment method, billing address, etc.)
            current_user (User): The user object that is creating the payment intent

        Returns:
            PaymentIntentResponse: Object containing the payment intent's client secret and ID

        Raises:
            PaymentMethodRequiredError: If the order doesn't have an associated payment method
            InvalidPaymentAmountError: If the order's total price is zero or negative
            PaymentIntentCreationError: If Stripe fails to create the payment intent
        """
        if current_user.id != order.buyer_id:
            raise UserNotAllowed(
                uuid=current_user.id,
                action="Create a payment intent for an order that is not yours",
            )
        if not order.payment_method_id:
            raise PaymentMethodRequiredError(order_id=order.id)

        if order.total_price <= 0:
            raise InvalidPaymentAmountError(
                amount=order.total_price, currency=order.currency
            )
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_price * 100),
                currency=order.currency,
                metadata={
                    "order_id": str(order.id),
                    "buyer_id": str(order.buyer_id),
                    "seller_id": str(order.seller_id),
                    "item_id": str(order.item_id),
                    "payment_method_id": str(order.payment_method_id),
                    "billing_address_id": str(order.billing_address_id),
                    "order_created_at": str(order.created_at),
                    "payment_status": order.payment_status,
                    "total_price": order.total_price,
                    "currency": order.currency,
                    "payment_intent_datetime": datetime.now().isoformat(),
                },
            )
            return PaymentIntentResponse(
                client_secret=intent.client_secret, payment_intent_id=intent.id
            )
        except stripe.error.StripeError as e:
            raise PaymentIntentCreationError(order_id=order.id, error_message=str(e))

    async def create_direct_payout(
        self,
        amount: float,
        bank_account: dict,
        currency: str = "AED",
        metadata: dict = None,
    ) -> dict:
        """
        Envoie un paiement direct vers le compte bancaire du vendeur
        """
        try:
            # Créer un destinataire externe
            external_account = stripe.ExternalAccount.create(
                account_holder_name=bank_account["holder_name"],
                account_holder_type="individual",
                account_number=bank_account["account_number"],
                routing_number=bank_account["routing_number"],
                country="AE",
                currency=currency,
            )

            # Créer le payout
            payout = stripe.Payout.create(
                amount=int(amount * 100),  # Conversion en centimes
                currency=currency,
                destination=external_account.id,
                metadata=metadata,
            )

            return {
                "payout_id": payout.id,
                "status": payout.status,
                "arrival_date": payout.arrival_date,
            }

        except stripe.error.StripeError as e:
            raise PayoutError(f"Failed to create payout: {str(e)}")

    @staticmethod
    async def confirm_payment(payment_intent_id: str) -> PaymentIntentResponse:
        """
        Confirm a Stripe payment intent.

        Args:
            payment_intent_id (str): ID of payment intent to confirm

        Returns:
            PaymentIntentResponse: Confirmed payment intent details

        Raises:
            PaymentIntentConfirmationError: If confirmation fails
        """
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)

            return PaymentIntentResponse(
                client_secret=intent.client_secret, payment_intent_id=intent.id
            )
        except stripe.error.StripeError as e:
            raise PaymentIntentConfirmationError(
                payment_intent_id=payment_intent_id, error_message=str(e)
            )
