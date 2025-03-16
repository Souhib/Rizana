import re
from datetime import datetime
from enum import Enum
from typing import Any, Self

import pycountry
import pydantic
from pydantic import EmailStr, model_validator
from sqlalchemy import JSON, Column
from sqlmodel import AutoString, Field

from rizana.api.models.shared import DBModel


class NotificationType(str, Enum):
    GENERAL = "general"
    MESSAGE = "message"
    ORDER_UPDATE = "order_update"


class AddressBase(DBModel):
    street: str
    city: str
    state: str | None = Field(default=None)
    country: str
    postal_code: str


class UserActivityLogBase(DBModel):
    action: str
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=255)
    details: dict[str, Any] | None = Field(default_factory=dict, sa_column=Column(JSON))


class NotificationBase(DBModel):
    message: str
    is_read: bool = Field(default=False)
    notification_type: NotificationType = Field(default=NotificationType.GENERAL)


class UserBase(DBModel):
    """
    Base model for User.

    Attributes:
        username (str): The username of the user.
        email (EmailStr): The email of the user.
        emirate_id (str | None): The emirate ID of the user.
        country (str | None): The country of the user, default is "ARE".
    """

    username: str = Field(default=None, index=True, min_length=3)
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    phone: str | None = Field(default=None, index=True, unique=True)
    emirate_id: str | None = Field(default=None, index=True, unique=True)
    country: str | None = "ARE"

    @pydantic.field_validator("country")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """
        Validates the country code.

        Args:
            v (str): The value to be validated.

        Returns:
            str: The validated country code.

        Raises:
            ValueError: If the country code is not valid.
        """
        if v and pycountry.countries.get(alpha_3=v.upper()) is None:
            raise ValueError("Country must be a valid 3-letter country code")
        return v

    @model_validator(mode="after")
    def validate_emirate_id(self) -> Self:
        """
        Validates that emirate_id is provided when country is ARE and checks its format.

        Returns:
            Self: The validated instance.

        Raises:
            ValueError: If emirate_id is required but not provided, or if its format is incorrect.
        """
        if self.country == "ARE" and self.emirate_id is None:
            raise ValueError("Emirate ID is required for users from UAE")
        if self.emirate_id is not None:
            if not re.match(r"^784-\d{4}-\d{7}-\d{1}$", self.emirate_id):
                raise ValueError("Format of Emirate ID is not correct")
        return self

    @model_validator(mode="after")
    def validate_phone(self) -> Self:
        """
        Validates that phone is provided when country is ARE and checks its format.

        Returns:
            Self: The validated instance.

        Raises:
            ValueError: If phone is required but not provided, or if its format is incorrect.
        """
        if self.country == "ARE" and self.phone:
            if not re.match(r"^\+971\d{9}$", self.phone):
                raise ValueError("Format of phone number is not correct")
        return self
