from datetime import datetime

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class WishlistBase(DBModel):
    created_at: datetime = Field(default_factory=datetime.now)
