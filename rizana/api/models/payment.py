import re
from datetime import datetime
from enum import Enum
from uuid import UUID

import pycountry
import pydantic
from sqlalchemy import JSON, Column
from sqlmodel import Field

from rizana.api.models.shared import DBModel


class CardType(str, Enum):
    """
    Enum representing different types of credit cards.

    Attributes:
        VISA (str): Visa credit card.
        MASTERCARD (str): MasterCard credit card.
        AMEX (str): American Express credit card.
        DISCOVER (str): Discover credit card.
    """

    VISA = "Visa"
    MASTERCARD = "MasterCard"
    AMEX = "American Express"
    DISCOVER = "Discover"


class PaymentMethodBase(DBModel):
    """
    Represents a base model for payment methods.
    Attributes:
        card_type (CardType): The type of the card (e.g., Visa, MasterCard).
        card_number (str): The card number. Secure storage required.
        expiry_date (str): The expiry date of the card in MM/YY format.
        cvv (str): The CVV code of the card. Secure storage required.
        holder_name (str): The name of the cardholder.
    """

    card_type: CardType
    card_number: str  # Secure storage required
    expiry_date: str
    cvv: str  # Secure storage required
    holder_name: str

    @pydantic.field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v: str):
        """
        Validates the expiry date format and checks if the date is not in the past.

        Args:
            cls: The class itself.
            v (str): The expiry date string in the format MM/YY.

        Returns:
            str: The validated expiry date string.

        Raises:
            ValueError: If the expiry date format is invalid or if the expiry date is in the past.
        """
        if not re.match(r"^(0[1-9]|1[0-2])/\d{2}$", v):
            raise ValueError("Invalid expiry date format. Use MM/YY")
        if datetime.now() > datetime.strptime(v, "%m/%y"):
            raise ValueError("Expiry date is in the past")
        return v


class BillingAddressBase(DBModel):
    billing_street: str = Field(max_length=100)
    billing_city: str = Field(max_length=50)
    billing_state: str = Field(default=None, max_length=50)
    billing_country: str = Field(max_length=3)
    billing_postal_code: str = Field(max_length=20)

    @pydantic.field_validator("billing_country")
    @classmethod
    def validate_country(cls, v: str | None):
        """
        Validates the given country code.

        Args:
            v (str | None): The country code to validate. It should be a 3-letter ISO code.

        Returns:
            str | None: The validated and uppercased country code if valid, otherwise None.

        Raises:
            ValueError: If the country code is not a 3-letter ISO code or if it is not a valid ISO country code.
        """
        if v is not None:
            if len(v) != 3 or not v.isalpha():
                raise ValueError("Country code must be a 3-letter ISO code")
            if pycountry.countries.get(alpha_3=v.upper()) is None:
                raise ValueError(f"Invalid country code: {v}")
        return v.upper() if v else v

    @pydantic.field_validator("billing_postal_code")
    @classmethod
    def validate_postal_code(cls, v: str | None):
        """
        Validates that the postal code contains only alphanumeric characters.

        Args:
            v (str | None): The postal code to validate.

        Returns:
            str | None: The validated postal code if it is valid, otherwise raises a ValueError.

        Raises:
            ValueError: If the postal code contains non-alphanumeric characters.
        """
        if v and not v.isalnum():
            raise ValueError("Postal code should only contain alphanumeric characters")
        return v


class PaymentBase(DBModel):
    order_id: UUID = Field(foreign_key="order.id")
    amount: float
    currency: str = Field(default="AED")
    description: str


class PaymentIntentCreate(PaymentBase):
    item_id: UUID
    item_name: str
    item_price: float


class BankAccountBase(DBModel):
    account_name: str
    account_number: str
    iban: str
    swift_code: str
    is_primary: bool = Field(default=False)


class StripeSellerAccountBase(DBModel):
    user_id: UUID = Field(foreign_key="user.id", unique=True)
    stripe_account_id: str = Field(unique=True)
    capabilities: dict = Field(default_factory=dict, sa_column=Column(JSON))
