import re
from enum import Enum

import pycountry
import pydantic
from sqlmodel import Field

from rizana.api.models.shared import DBModel


class CardType(Enum):
    VISA = "Visa"
    MASTERCARD = "MasterCard"
    AMEX = "American Express"
    DISCOVER = "Discover"


class PaymentMethodBase(DBModel):
    card_type: CardType
    card_number: str  # Secure storage required
    expiry_date: str
    billing_street: str | None = Field(default=None, max_length=100)
    billing_city: str | None = Field(default=None, max_length=50)
    billing_state: str | None = Field(default=None, max_length=50)
    billing_country: str | None = Field(default=None, max_length=3)
    billing_postal_code: str | None = Field(default=None, max_length=20)

    @pydantic.field_validator("billing_country")
    @classmethod
    def validate_country(cls, v: str | None):
        if v is not None:
            if len(v) != 3 or not v.isalpha():
                raise ValueError("Country code must be a 3-letter ISO code")
            if pycountry.countries.get(alpha_3=v.upper()) is None:
                raise ValueError(f"Invalid country code: {v}")
        return v.upper() if v else v

    @pydantic.field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str):
        if not v.isdigit() or len(v) < 13 or len(v) > 19:
            raise ValueError("Invalid card number")
        return v

    @pydantic.field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v: str):
        if not re.match(r"^(0[1-9]|1[0-2])/\d{2}$", v):
            raise ValueError("Invalid expiry date format. Use MM/YY")
        return v

    @pydantic.field_validator("billing_postal_code")
    @classmethod
    def validate_postal_code(cls, v: str | None):
        if v and not v.isalnum():
            raise ValueError("Postal code should only contain alphanumeric characters")
        return v
