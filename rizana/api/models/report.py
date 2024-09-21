from enum import Enum

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class ReportBase(DBModel):
    reason: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    status: ReportStatus = Field(default=ReportStatus.PENDING)
