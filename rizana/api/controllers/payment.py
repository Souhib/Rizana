from typing import Sequence
from uuid import UUID

from argon2 import PasswordHasher
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.table import BillingAddress, PaymentMethod, User
from rizana.api.schemas.error import (PaymentMethodCreationError,
                                      PaymentMethodDoesNotExist,
                                      UserNotAllowed)
from rizana.api.schemas.payment import PaymentMethodCreate


class PaymentController:
    """
    Handles payment-related operations such as creating, deleting, and retrieving payment methods.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the PaymentController with a database session.

        Args:
            db (AsyncSession): The database session to use for operations.
        """
        self.db = db
        self.ph = PasswordHasher()

    async def create_payment(self, payment_data: PaymentMethodCreate, user_id: UUID):
        """
        Creates a new payment method.

        This method attempts to create a new payment method with the provided data and associates it with the given user ID.
        If the creation is successful, it returns the newly created payment method object. If not, it raises a PaymentMethodCreationError.

        Args:
            payment_data (PaymentMethodCreate): The payment method creation schema.
            user_id (UUID): The ID of the user to associate the payment method with.

        Returns:
            PaymentMethod: The newly created payment method object.

        Raises:
            PaymentMethodCreationError: If the payment method creation fails due to an integrity error.
        """
        try:
            new_payment = PaymentMethod(**payment_data.model_dump(), user_id=user_id)
            new_payment.card_number = await self._hash_card_number(
                new_payment.card_number
            )
            self.db.add(new_payment)
            await self.db.commit()
            await self.db.refresh(new_payment)
            return new_payment
        except IntegrityError as e:
            await self.db.rollback()
            raise PaymentMethodCreationError(user_id=user_id) from e

    async def delete_payment_method(self, payment_method_id: UUID, current_user: User):
        """
        Deletes a payment method by ID.

        This method attempts to delete a payment method by its ID. If the payment method belongs to the current user, it is deleted.
        If not, it raises a UserNotAllowed error. If the payment method does not exist, it raises a PaymentMethodDoesNotExist error.

        Args:
            payment_method_id (UUID): The ID of the payment method to delete.
            current_user (User): The user attempting to delete the payment method.

        Raises:
            UserNotAllowed: If the payment method does not belong to the current user.
            PaymentMethodDoesNotExist: If the payment method does not exist.
        """
        try:
            payment_method = (
                await self.db.exec(
                    select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
                )
            ).one()
            if payment_method.user_id != current_user.id:
                raise UserNotAllowed(
                    uuid=current_user.id,  # type: ignore
                    action="delete a payment method that is not yours",
                )
            await self.db.delete(payment_method)
            await self.db.commit()
        except NoResultFound:
            raise PaymentMethodDoesNotExist(payment_method_id=payment_method_id)
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_payments_method(self, current_user: User) -> Sequence[PaymentMethod]:
        """
        Retrieves all payment methods associated with the current user.

        This method fetches all payment methods belonging to the current user.

        Args:
            current_user (User): The user whose payment methods to retrieve.

        Returns:
            Sequence[PaymentMethod]: A list of payment methods associated with the current user.
        """
        return (
            await self.db.exec(
                select(PaymentMethod).where(PaymentMethod.user_id == current_user.id)
            )
        ).all()

    async def get_payment_method(self, payment_method_id: UUID) -> PaymentMethod:
        """
        Retrieves a payment method by its ID.

        This method executes a database query to fetch a payment method by its unique identifier.
        If a payment method with the specified ID exists, it returns the payment method object.
        If not, it raises a NoResultFound exception.

        Args:
            payment_method_id (UUID): The unique identifier of the payment method to retrieve.

        Returns:
            PaymentMethod: The payment method object associated with the provided ID.

        Raises:
            NoResultFound: If no payment method with the specified ID is found.
        """
        return (
            await self.db.exec(
                select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
            )
        ).one()

    async def _hash_card_number(self, card_number: str) -> str:
        """
        Hashes a card number for secure storage.

        This method uses the Argon2 password hasher to hash a card number for secure storage.

        Args:
            card_number (str): The card number to hash.

        Returns:
            str: The hashed card number.
        """
        return self.ph.hash(card_number)

    async def get_billing_address(self, current_user: User) -> BillingAddress:
        """
        Retrieves the billing address associated with the current user.

        This method executes a database query to fetch the billing address linked to the current user.
        It returns the billing address object if found, otherwise, it raises a NoResultFound exception.

        Args:
            current_user (User): The user whose billing address to retrieve.

        Returns:
            BillingAddress: The billing address object associated with the current user.

        Raises:
            NoResultFound: If no billing address is found for the specified user.
        """
        return (
            await self.db.exec(
                select(BillingAddress).where(BillingAddress.user_id == current_user.id)
            )
        ).one()
