import pydantic

from rizana.api.models.order import CharityContributionBase
from rizana.api.models.payment import (
    BankAccountBase,
    BillingAddressBase,
    PaymentMethodBase,
)


class PaymentMethodCreate(PaymentMethodBase):
    """
    Represents a payment method creation request.

    This class extends `PaymentMethodBase` and adds validation for the `card_number` field.
    """

    @pydantic.field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str):
        """
        Validates the `card_number` field.

        This method checks if the `card_number` is a digit-only string and its length is between 13 and 19 characters.
        If the validation fails, it raises a `ValueError`.

        Args:
            v (str): The value of the `card_number` field to be validated.

        Returns:
            str: The validated `card_number` value.

        Raises:
            ValueError: If the `card_number` is invalid.
        """
        if len(v) < 12 or len(v) > 19:
            raise ValueError("Invalid card number")
        return v


class BillingAddressCreate(BillingAddressBase): ...


class CharityContributionCreate(CharityContributionBase): ...


class BankAccountCreate(BankAccountBase): ...
