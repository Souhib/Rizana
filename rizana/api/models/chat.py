from datetime import datetime

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class ChatBase(DBModel):
    message: str
    sent_at: datetime = Field(default_factory=datetime.now)
    is_read: bool = Field(default=False)
