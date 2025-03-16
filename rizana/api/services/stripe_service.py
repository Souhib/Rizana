from datetime import datetime
from uuid import UUID

import stripe
from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.stripe import PaymentIntentResponse
from rizana.api.models.table import Order, User, Payout

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
        self, db: AsyncSession,
        stripe_api_key: str, frontend_success_url: str, frontend_cancel_url: str
    ):
        self.db = db
        self._set_stripe_api_key(stripe_api_key)
        self.success_url = frontend_success_url
        self.cancel_url = frontend_cancel_url
        self.PLATFORM_FEE_PERCENTAGE = 0.05  # 5% taken from seller's amount
        self.TAX_PERCENTAGE = 0.05  # 5% added on top for buyer

    def _set_stripe_api_key(self, stripe_api_key: str) -> None:
        """
        Sets the Stripe API key for the service.

        Args:
            stripe_api_key (str): The Stripe API key to be set.
        """
        stripe.api_key = stripe_api_key

    async def create_seller_account(self, seller: User) -> dict:
        """Creates a Stripe Connect account for a seller."""
        try:
            # Create a Standard Connect account
            account = stripe.Account.create(
                type="standard",
                country="AE",
                email=seller.email,
                business_type="individual",
                capabilities={
                    "transfers": {"requested": True},
                    "card_payments": {"requested": True},
                },
                metadata={
                    "seller_id": str(seller.id),
                    "emirate_id": seller.emirate_id if seller.emirate_id else "",
                }
            )

            # Save the account details in our database
            seller_account = SellerAccount(
                user_id=seller.id,
                stripe_account_id=account.id,
                status="pending",
                capabilities=account.capabilities,
            )
            self.db.add(seller_account)
            await self.db.commit()

            # Generate onboarding link
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=f"{self.cancel_url}/connect/reauth",
                return_url=f"{self.success_url}/connect/return",
                type="account_onboarding",
            )

            return {
                "account_id": account.id,
                "onboarding_url": account_link.url,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe account creation failed: {str(e)}")
            raise StripeAccountCreationError(seller_id=seller.id, error_message=str(e))

    async def get_seller_account_status(self, seller: User) -> dict:
        """Gets the verification status of a seller's Stripe account."""
        seller_account = await self.db.exec(
            select(SellerAccount).where(SellerAccount.user_id == seller.id)
        ).first()

        if not seller_account:
            return {"status": "not_created"}

        try:
            account = stripe.Account.retrieve(seller_account.stripe_account_id)

            # Update local status
            seller_account.status = "verified" if account.charges_enabled else "pending"
            seller_account.capabilities = account.capabilities
            await self.db.commit()

            return {
                "status": seller_account.status,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "requirements": account.requirements,
                "capabilities": account.capabilities,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to check account status: {str(e)}")
            return {"status": "error", "error": str(e)}


    async def create_payment_intent(
        self, order: Order, current_user: User
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

        base_amount = order.total_price
        tax_amount = base_amount * self.TAX_PERCENTAGE
        total_amount_with_tax = base_amount + tax_amount
        charity_amount = order.charity_contribution.amount if order.charity_contribution else 0
        total_amount_with_charity = total_amount_with_tax + charity_amount

        if order.total_price <= 0:
            raise InvalidPaymentAmountError(
                amount=order.total_price, currency=order.currency
            )
        try:
            customer = stripe.Customer.create(
                email=order.buyer.email,
                name=order.buyer.username,
                phone=order.buyer.phone if order.buyer.phone else "",
                metadata={
                    "user_id": str(order.buyer_id),
                    "emirate_id": order.buyer.emirate_id if order.buyer.emirate_id else "",
                    "country": order.buyer.country
                }
            )
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_price * 100),
                currency=order.currency,
                metadata={
                    "order_id": str(order.id),
                    "buyer_id": str(order.buyer_id),
                    "seller_id": str(order.seller_id),
                    "item_id": str(order.item_id),
                    "item_initial_price": order.item.price,
                    "base_amount": base_amount,
                    "tax_amount": tax_amount,
                    "charity_amount": charity_amount,
                    "total_amount_with_tax": total_amount_with_tax,
                    "total_amount": total_amount_with_charity,
                    "payment_method_id": str(order.payment_method_id),
                    "billing_address_id": str(order.billing_address_id),
                    "order_created_at": str(order.created_at),
                    "currency": order.currency,
                    "payment_intent_datetime": datetime.now().isoformat(),
                },
                description=f"Order {order.id} - {order.item.title}",
            )
            return PaymentIntentResponse(
                client_secret=intent.client_secret, payment_intent_id=intent.id
            )
        except stripe.error.StripeError as e:
            raise PaymentIntentCreationError(order_id=order.id, error_message=str(e))

    async def process_seller_payout(
        self,
        order: Order,
        payment_intent_id: str,
    ) -> dict:
        """
        Process payout to seller using their primary bank account details.
        For an item priced at 100 AED:
        - Seller receives 95 AED (original price - 5% platform fee)
        """
        try:
            # Get seller's primary bank account
            primary_bank_account = next(
                (acc for acc in order.seller.bank_accounts if acc.is_primary),
                None,
            )
            if not primary_bank_account:
                raise PayoutError(
                    f"No primary bank account found for seller {order.seller_id}"
                )

            base_amount = order.total_price
            platform_fee = base_amount * self.PLATFORM_FEE_PERCENTAGE
            seller_amount = base_amount - platform_fee  # 95% of base amount

            # First create payout record in database
            payout = Payout(
                order_id=order.id,
                seller_id=order.seller_id,
                bank_account_id=primary_bank_account.id,
                base_amount=base_amount,
                platform_fee=platform_fee,
                seller_amount=seller_amount,
                currency=order.currency,
                status="processing"
            )
            self.db.add(payout)
            await self.db.commit()
            await self.db.refresh(payout)

            try:
                # Create bank account token
                bank_account = {
                    "country": "AE",
                    "currency": "AED",
                    "account_holder_name": primary_bank_account.account_name,
                    "account_holder_type": "individual",
                    "account_number": primary_bank_account.account_number if primary_bank_account.account_number else "000123456789",
                    "routing_number": primary_bank_account.swift_code if primary_bank_account.swift_code else "TESTAEXX",
                }

                # Create the Stripe payout
                stripe_payout = stripe.Payout.create(
                    amount=int(seller_amount * 100),  # Convert to cents
                    currency=order.currency,
                    method="standard",
                    destination=bank_account,
                    metadata={
                        "payout_id": str(payout.id),
                        "order_id": str(order.id),
                        "payment_intent_id": payment_intent_id,
                        "seller_id": str(order.seller.id),
                        "bank_account_id": str(primary_bank_account.id),
                    },
                    description=f"Payout for order {order.id}",
                )

                # Update payout record with Stripe details
                payout.stripe_payout_id = stripe_payout.id
                payout.status = "completed"
                payout.processed_at = datetime.now()
                await self.db.commit()

                return {
                    "payout_id": payout.id,
                    "stripe_payout_id": stripe_payout.id,
                    "status": "completed",
                    "base_amount": base_amount,
                    "seller_amount": seller_amount,
                    "platform_fee": platform_fee,
                    "currency": order.currency,
                }

            except stripe.error.StripeError as e:
                # Update payout record with error
                payout.status = "failed"
                payout.error_message = str(e)
                await self.db.commit()
                raise PayoutError(
                    f"Failed to process seller payout for order {order.id}: {str(e)}"
                )

        except Exception as e:
            raise PayoutError(str(e))

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntentResponse:
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
            # First retrieve the payment intent to check its status
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # If not already succeeded, try to confirm
            if intent.status != 'succeeded':
                intent = stripe.PaymentIntent.confirm(payment_intent_id)

            # Convert string order_id to UUID
            order_id = UUID(intent.metadata.get("order_id"))
            order = (await self.db.exec(select(Order).where(Order.id == order_id))).one()  # type: ignore

            if order and order.payment_status != "paid":
                order.payment_status = "paid"
                order.stripe_payment_intent_id = intent.id
                await self.db.flush()
                await self.process_seller_payout(order, intent.id)

            return PaymentIntentResponse(
                client_secret=intent.client_secret,
                payment_intent_id=intent.id
            )
        except stripe.error.StripeError as e:
            logger.exception(f"Stripe error during payment confirmation: {str(e)}")
            raise PaymentIntentConfirmationError(
                payment_intent_id=payment_intent_id,
                error_message=str(e)
            )
        except ValueError as e:
            logger.exception(f"Invalid UUID format in order_id: {str(e)}")
            raise PaymentIntentConfirmationError(
                payment_intent_id=payment_intent_id,
                error_message="Invalid order ID format"
            )
        except Exception as e:
            logger.exception(f"Unexpected error during payment confirmation: {str(e)}")
            raise PaymentIntentConfirmationError(
                payment_intent_id=payment_intent_id,
                error_message="An unexpected error occurred"
            )