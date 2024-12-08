from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator

from rizana.api.models.chat import MessageBase, ProposalBase


class ProposalStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class MessageCreate(MessageBase):
    item_id: UUID | None = None
    conversation_id: UUID | None = None

    @model_validator(mode="after")
    def validate_emirate_id(self) -> Self:
        """
        Validates that either `item_id` or `conversation_id` is provided.

        This method is called after the model is initialized to ensure that at least
        one of `item_id` or `conversation_id` is not None. If both are None, a
        `ValueError` is raised.

        Returns:
            Self: The validated instance of the model.

        Raises:
            ValueError: If both `item_id` and `conversation_id` are None.
        """
        if self.item_id is None and self.conversation_id is None:
            raise ValueError("Either item_id or conversation_id is required")
        return self


class MessageResponse(MessageBase):
    id: UUID


class ProposalCreate(ProposalBase):
    item_id: UUID | None = None
    conversation_id: UUID | None = None

    @model_validator(mode="after")
    def validate_emirate_id(self) -> Self:
        """
        Validates that either `item_id` or `conversation_id` is provided.

        This method is called after the model is initialized to ensure that at least
        one of `item_id` or `conversation_id` is not None. If both are None, a
        `ValueError` is raised.

        Returns:
            Self: The validated instance of the model.

        Raises:
            ValueError: If both `item_id` and `conversation_id` are None.
        """
        if self.item_id is None and self.conversation_id is None:
            raise ValueError("Either item_id or conversation_id is required")
        return self


class ProposalResponse(ProposalBase):
    id: UUID
    sender_id: UUID
    item_id: UUID
    proposed_price: float
    status: ProposalStatus
    created_at: datetime


class ConversationResponse(BaseModel):
    messages: list[MessageResponse]
    proposals: list[ProposalResponse]
