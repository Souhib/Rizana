from datetime import datetime, timedelta
from uuid import UUID

import stripe
from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.stripe import PaymentIntentResponse
from rizana.api.models.table import Order, Payout, StripeSellerAccount, User
from rizana.api.schemas.error import (
    InvalidPaymentAmountError,
    PaymentIntentConfirmationError,
    PaymentIntentCreationError,
    PaymentMethodRequiredError,
    PayoutError,
    StripeSellerAccountCreationError,
    UserNotAllowed,
)


class StripeService:

    def __init__(
        self,
        db: AsyncSession,
        stripe_api_key: str,
        frontend_success_url: str,
        frontend_cancel_url: str,
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

    # async def initiate_seller_onboarding(self, seller: User) -> dict:
    #     """Creates a Stripe account and returns an onboarding URL"""
    #     try:
    #         account = stripe.Account.create(
    #             type="standard",
    #             country="AE",
    #             email=seller.email,
    #             metadata={
    #                 "seller_id": str(seller.id),
    #                 "username": seller.username,
    #             },
    #             capabilities={
    #                 "card_payments": {"requested": True},
    #                 "transfers": {"requested": True},
    #             },
    #         )
    #
    #         # Generate onboarding link
    #         account_link = stripe.AccountLink.create(
    #             account=account.id,
    #             refresh_url="http://localhost:8000/seller/reauth",
    #             return_url="http://localhost:8000/seller/complete",
    #             type="account_onboarding",
    #             collect="eventually_due",  # Only collect essential info initially
    #         )
    #
    #         # Save account details
    #         seller_account = StripeSellerAccount(
    #             user_id=seller.id,
    #             stripe_account_id=account.id,
    #             status="pending"
    #         )
    #         self.db.add(seller_account)
    #
    #         # Update user
    #         seller.is_seller = True
    #         seller.seller_status = "pending"
    #         seller.seller_verification_url = account_link.url
    #         seller.seller_verification_expires_at = datetime.now() + timedelta(days=7)
    #
    #         await self.db.commit()
    #
    #         return {
    #             "verification_url": account_link.url,
    #             "expires_at": seller.seller_verification_expires_at,
    #             "account_id": account.id
    #         }
    #
    #     except stripe.error.StripeError as e:
    #         logger.error(f"Stripe seller onboarding failed: {str(e)}")
    #         raise StripeSellerAccountCreationError(
    #             seller_id=seller.id, error_message=str(e)
    #         )

    async def create_seller_account(self, seller: User, with_onboarding: bool = True) -> dict:
        """Creates a Stripe Connect account for a seller following UAE regulations.

        Args:
            seller: The seller user object
            with_onboarding: If True, generates onboarding URL and updates user model

        UAE Requirements:
        - Emirates ID
        - Valid UAE phone number
        - Business/Trade license for commercial activities
        - Bank account in UAE
        - Proof of address
        """
        if not seller.emirate_id or not seller.phone:
            raise StripeSellerAccountCreationError(
                seller_id=seller.id,
                error_message="Emirates ID and UAE phone number are required for seller registration"
            )

        try:
            # Create Stripe account with UAE-specific requirements
            account = stripe.Account.create(
                type="standard",  # Standard account type is recommended for UAE
                country="AE",
                email=seller.email,
                business_type="individual",  # or "company" if supporting business accounts
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={
                    "seller_id": str(seller.id),
                    "username": seller.username,
                    "email": seller.email,
                    "phone": seller.phone,
                    "emirate_id": seller.emirate_id,
                    "country": "ARE",  # UAE specific
                    "account_created_at": str(seller.created_at),
                    "stripe_account_created_at": datetime.now().isoformat(),
                },
                business_profile={
                    "mcc": "5691",  # Merchant Category Code for clothing stores
                    "url": "your-website.com",  # Replace with actual marketplace URL
                    "support_email": seller.email,
                    "support_phone": seller.phone,
                },
                settings={
                    "payouts": {
                        "schedule": {
                            "interval": "manual"  # Manual payouts for initial verification
                        },
                        "statement_descriptor": "RIZANA MARKETPLACE",  # Should match your business name
                    }
                }
            )

            # Save account details
            seller_account = StripeSellerAccount(
                user_id=seller.id,
                stripe_account_id=account.id,
                status="pending",
                capabilities=account.capabilities,
            )
            self.db.add(seller_account)

            response = {
                "account_id": account.id,
                "status": "pending"
            }

            # Generate onboarding if requested
            if with_onboarding:
                account_link = stripe.AccountLink.create(
                    account=account.id,
                    refresh_url=f"{self.cancel_url}/seller/reauth",
                    return_url=f"{self.success_url}/seller/complete",
                    type="account_onboarding",
                    collect="eventually_due",
                    # UAE specific requirements that must be collected
                    collect_requirements={
                        "currently_due": [
                            "external_account",  # Bank account details
                            "individual.id_number",  # Emirates ID
                            "individual.phone",  # Phone verification
                            "individual.email",  # Email verification
                            "individual.first_name",
                            "individual.last_name",
                            "individual.dob.day",
                            "individual.dob.month",
                            "individual.dob.year",
                            "individual.address.city",
                            "individual.address.line1",
                            "individual.address.postal_code",
                            "individual.verification.document",  # ID verification
                            "tos_acceptance.date",
                            "tos_acceptance.ip",
                        ]
                    }
                )

                # Update user model
                seller.is_seller = True
                seller.seller_status = "pending"
                seller.seller_verification_url = account_link.url
                seller.seller_verification_expires_at = datetime.now() + timedelta(days=7)

                response.update({
                    "verification_url": account_link.url,
                    "expires_at": seller.seller_verification_expires_at,
                    "requirements": {
                        "emirates_id_required": True,
                        "phone_verification_required": True,
                        "address_verification_required": True,
                        "bank_account_required": True,
                        "document_verification_required": True
                    }
                })

            await self.db.commit()
            return response

        except stripe.error.StripeError as e:
            logger.error(f"Stripe account creation failed: {str(e)}")
            raise StripeSellerAccountCreationError(
                seller_id=seller.id, error_message=str(e)
            )

    async def get_seller_account_status(self, seller: User) -> dict:
        """Gets the verification status of a seller's Stripe account with UAE-specific details."""
        seller_account = await self.db.exec(
            select(StripeSellerAccount).where(StripeSellerAccount.user_id == seller.id)  # type: ignore
        ).first()

        if not seller_account:
            return {"status": "not_created"}

        try:
            account = stripe.Account.retrieve(seller_account.stripe_account_id)

            # Update local status
            seller_account.status = "verified" if account.charges_enabled else "pending"
            seller_account.capabilities = account.capabilities
            await self.db.commit()

            # Include UAE-specific verification details
            return {
                "status": seller_account.status,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "requirements": account.requirements,
                "capabilities": account.capabilities,
                "verification_details": {
                    "emirates_id_verified": account.individual.verification.status if hasattr(account,
                                                                                              'individual') else None,
                    "address_verified": account.individual.address.verified if hasattr(account, 'individual') else None,
                    "phone_verified": account.individual.phone_verified if hasattr(account, 'individual') else None,
                    "external_account_verified": bool(account.external_accounts.total_count) if hasattr(account,
                                                                                                        'external_accounts') else None
                }
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to check account status: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def create_payment_intent(
            self, order: Order, current_user: User
    ) -> PaymentIntentResponse:
        if current_user.id != order.buyer_id:
            raise UserNotAllowed(
                uuid=current_user.id,
                action="Create a payment intent for an order that is not yours",
            )
        if not order.payment_method_id:
            raise PaymentMethodRequiredError(order_id=order.id)

        # Get seller's Stripe account
        seller_account = (await self.db.exec(
            select(StripeSellerAccount).where(StripeSellerAccount.user_id == order.seller_id)  # type: ignore
        )).first()

        # If seller doesn't have a Stripe account, create one
        if not seller_account:
            try:
                # Create a Custom Connect account
                account = stripe.Account.create(
                    type="standard",
                    country="AE",
                    email=order.seller.email,
                    business_type="individual",
                    capabilities={
                        "transfers": {"requested": True},
                        "card_payments": {"requested": True},
                    },
                    tos_acceptance={
                        "date": int(datetime.now().timestamp()),
                        "ip": "127.0.0.1",  # You should pass the real IP in production
                    },
                    business_profile={
                        "mcc": "5691",  # Merchant Category Code for clothing stores
                        "url": "your-website.com",
                    },
                    metadata={
                        "seller_id": str(order.seller_id),
                        "username": order.seller.username,
                        "email": order.seller.email,
                        "phone": order.seller.phone or "",
                        "emirate_id": order.seller.emirate_id or "",
                        "country": order.seller.country,
                        "account_created_at": str(order.seller.created_at),
                        "stripe_account_created_at": datetime.now().isoformat(),
                    }
                )

                # Save the account details in our database
                seller_account = StripeSellerAccount(
                    user_id=order.seller_id,
                    stripe_account_id=account.id,
                    status="active",
                    capabilities=account.capabilities,
                )
                self.db.add(seller_account)
                await self.db.commit()

            except stripe.error.StripeError as e:
                raise PaymentIntentCreationError(
                    order_id=order.id,
                    error_message=f"Failed to create seller Stripe account: {str(e)}"
                )

        base_amount = order.total_price
        tax_amount = base_amount * self.TAX_PERCENTAGE
        total_amount_with_tax = base_amount + tax_amount
        platform_fee = int(base_amount * self.PLATFORM_FEE_PERCENTAGE * 100)  # in cents
        charity_amount = (
            order.charity_contribution.amount if order.charity_contribution else 0
        )
        total_amount = total_amount_with_tax + charity_amount

        if order.total_price <= 0:
            raise InvalidPaymentAmountError(
                amount=order.total_price, currency=order.currency
            )

        try:
            # Create or get customer
            customer = stripe.Customer.create(
                email=order.buyer.email,
                name=order.buyer.username,
                phone=order.buyer.phone if order.buyer.phone else "",
                metadata={
                    "user_id": str(order.buyer_id),
                    "emirate_id": order.buyer.emirate_id if order.buyer.emirate_id else "",
                    "country": order.buyer.country,
                },
            )

            # Create payment intent with automatic transfer to seller
            intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),  # total amount in cents
                currency=order.currency.lower(),
                customer=customer.id,
                application_fee_amount=platform_fee,  # Platform's 5% fee
                transfer_data={
                    "destination": seller_account.stripe_account_id,  # Automatic transfer to seller
                },
                metadata={
                    "order_id": str(order.id),
                    "buyer_id": str(order.buyer_id),
                    "seller_id": str(order.seller_id),
                    "item_id": str(order.item_id),
                    "item_initial_price": str(order.item.price),
                    "base_amount": str(base_amount),
                    "tax_amount": str(tax_amount),
                    "platform_fee": str(platform_fee / 100),  # Convert back to decimal
                    "charity_amount": str(charity_amount),
                    "total_amount": str(total_amount),
                    "payment_method_id": str(order.payment_method_id),
                    "billing_address_id": str(order.billing_address_id),
                    "order_created_at": str(order.created_at),
                    "currency": order.currency,
                    "payment_intent_datetime": datetime.now().isoformat(),
                },
                description=f"Order {order.id} - {order.item.title}",
            )

            return PaymentIntentResponse(
                client_secret=intent.client_secret,
                payment_intent_id=intent.id
            )

        except stripe.error.StripeError as e:
            raise PaymentIntentCreationError(order_id=order.id, error_message=str(e))

    # async def process_seller_payout(
    #     self,
    #     order: Order,
    #     payment_intent_id: str,
    # ) -> dict:
    #     """
    #     Process payout to seller using their primary bank account details.
    #     For an item priced at 100 AED:
    #     - Seller receives 95 AED (original price - 5% platform fee)
    #     """
    #     try:
    #         # Get seller's primary bank account
    #         primary_bank_account = next(
    #             (acc for acc in order.seller.bank_accounts if acc.is_primary),
    #             None,
    #         )
    #         if not primary_bank_account:
    #             raise PayoutError(
    #                 f"No primary bank account found for seller {order.seller_id}"
    #             )
    #
    #         base_amount = order.total_price
    #         platform_fee = base_amount * self.PLATFORM_FEE_PERCENTAGE
    #         seller_amount = base_amount - platform_fee  # 95% of base amount
    #
    #         # First create payout record in database
    #         payout = Payout(
    #             order_id=order.id,
    #             seller_id=order.seller_id,
    #             bank_account_id=primary_bank_account.id,
    #             base_amount=base_amount,
    #             platform_fee=platform_fee,
    #             seller_amount=seller_amount,
    #             currency=order.currency,
    #             status="processing",
    #         )
    #         self.db.add(payout)
    #         await self.db.commit()
    #         await self.db.refresh(payout)
    #
    #         try:
    #             # Create bank account token
    #             bank_account = {
    #                 "country": "AE",
    #                 "currency": "AED",
    #                 "account_holder_name": primary_bank_account.account_name,
    #                 "account_holder_type": "individual",
    #                 "account_number": (
    #                     primary_bank_account.account_number
    #                     if primary_bank_account.account_number
    #                     else "000123456789"
    #                 ),
    #                 "routing_number": (
    #                     primary_bank_account.swift_code
    #                     if primary_bank_account.swift_code
    #                     else "TESTAEXX"
    #                 ),
    #             }
    #
    #             # Create the Stripe payout
    #             stripe_payout = stripe.Payout.create(
    #                 amount=int(seller_amount * 100),  # Convert to cents
    #                 currency=order.currency,
    #                 method="standard",
    #                 destination=bank_account,
    #                 metadata={
    #                     "payout_id": str(payout.id),
    #                     "order_id": str(order.id),
    #                     "payment_intent_id": payment_intent_id,
    #                     "seller_id": str(order.seller.id),
    #                     "bank_account_id": str(primary_bank_account.id),
    #                 },
    #                 description=f"Payout for order {order.id}",
    #             )
    #
    #             # Update payout record with Stripe details
    #             payout.stripe_payout_id = stripe_payout.id
    #             payout.status = "completed"
    #             payout.processed_at = datetime.now()
    #             await self.db.commit()
    #
    #             return {
    #                 "payout_id": payout.id,
    #                 "stripe_payout_id": stripe_payout.id,
    #                 "status": "completed",
    #                 "base_amount": base_amount,
    #                 "seller_amount": seller_amount,
    #                 "platform_fee": platform_fee,
    #                 "currency": order.currency,
    #             }
    #
    #         except stripe.error.StripeError as e:
    #             # Update payout record with error
    #             payout.status = "failed"
    #             payout.error_message = str(e)
    #             await self.db.commit()
    #             raise PayoutError(
    #                 f"Failed to process seller payout for order {order.id}: {str(e)}"
    #             )
    #
    #     except Exception as e:
    #         raise PayoutError(str(e))

    async def confirm_payment(self, payment_intent_id: str) -> PaymentIntentResponse:
        """
        Confirm a Stripe payment intent. With Connect, transfers happen automatically.
        We just need to update our database records.
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Convert string order_id to UUID
            order_id = UUID(intent.metadata.get("order_id"))
            order = (await self.db.exec(select(Order).where(Order.id == order_id))).one()  # type: ignore

            if order and order.payment_status != "paid" and intent.status == "succeeded":
                # Update order status
                order.payment_status = "paid"
                order.stripe_payment_intent_id = intent.id

                # Create payout record (for our records only)
                payout = Payout(
                    order_id=order.id,
                    seller_id=order.seller_id,
                    base_amount=float(intent.metadata.get("base_amount")),
                    platform_fee=float(intent.metadata.get("platform_fee")),
                    seller_amount=float(intent.metadata.get("base_amount")) - float(
                        intent.metadata.get("platform_fee")),
                    currency=order.currency,
                    status="completed",
                    stripe_payment_intent_id=intent.id,
                    bank_account_id=order.seller.bank_accounts[0].id,
                    processed_at=datetime.now()
                )
                self.db.add(payout)
                await self.db.commit()

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
