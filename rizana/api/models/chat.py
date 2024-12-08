from uuid import UUID

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class ConversationBase(DBModel):
    item_id: UUID = Field(foreign_key="item.id")
    buyer_id: UUID = Field(foreign_key="user.id")
    seller_id: UUID = Field(foreign_key="user.id")


class MessageBase(DBModel):
    message: str = Field(min_length=1)
    receiver_id: UUID | None = Field(foreign_key="user.id")


class ProposalBase(DBModel):
    proposed_price: float = Field(gt=0)
    receiver_id: UUID | None = Field(foreign_key="user.id")
