from datetime import datetime
from enum import Enum

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class BaseItem(DBModel):
    title: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0)


class CategoryBase(DBModel):
    name: str = Field(unique=True, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class FavoriteBase(DBModel):
    created_at: datetime = Field(default_factory=datetime.now)


class ItemCondition(str, Enum):
    NEW_WITH_TAGS = "New with tags"
    NEW_WITHOUT_TAGS = "New without tags"
    LIKE_NEW = "Like new"
    VERY_GOOD = "Very good"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class ItemConditionBase(DBModel):
    name: ItemCondition
    description: str | None = Field(default=None, max_length=255)
    wear_and_tear: str | None = Field(default=None, max_length=255)
    original_packaging: bool = Field(default=False)
    signs_of_use: str | None = Field(default=None, max_length=255)


class FeedbackType(str, Enum):
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"


class FeedbackBase(DBModel):
    rating: int = Field(default=5)
    comment: str | None = Field(default=None, max_length=1000)
    feedback_type: FeedbackType = Field(default=FeedbackType.GENERAL)
    is_resolved: bool = Field(default=False)
