from datetime import datetime
from enum import Enum

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"


class OrderBase(DBModel):
    item_id: int = Field(foreign_key="item.id")
    total_price: float
    created_at: datetime = Field(default_factory=datetime.now)
    status: OrderStatus = Field(default=OrderStatus.PENDING)


class DiscountBase(DBModel):
    code: str = Field(unique=True, max_length=20)
    description: str | None = Field(default=None, max_length=255)
    discount_percentage: float
    start_date: datetime
    end_date: datetime
    is_active: bool = Field(default=True)
