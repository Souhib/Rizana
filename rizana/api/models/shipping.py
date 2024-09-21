from datetime import datetime
from enum import Enum

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class ShippingMethod(str, Enum):
    STANDARD = "Standard"
    EXPRESS = "Express"


class ShippingStatus(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class ShippingBase(DBModel):
    shipping_method: ShippingMethod
    tracking_number: str | None = Field(default=None, max_length=50)
    shipping_date: datetime | None = Field(default=None)
    delivery_date: datetime | None = Field(default=None)
    status: ShippingStatus = Field(default=ShippingStatus.PENDING)
