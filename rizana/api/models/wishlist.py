from uuid import UUID

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class WishBase(DBModel):
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    item_id: UUID = Field(foreign_key="item.id", primary_key=True)
