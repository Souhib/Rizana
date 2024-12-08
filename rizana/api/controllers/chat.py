from datetime import datetime
from uuid import UUID

import sqlalchemy
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.item import ItemController
from rizana.api.controllers.order import OrderController
from rizana.api.controllers.user import UserController
from rizana.api.models.table import Conversation, Message, Proposal
from rizana.api.schemas.chat import MessageCreate, ProposalCreate, ProposalStatus
from rizana.api.schemas.error import (
    ConversationNotFoundError,
    ConversationNotFoundErrorByUsers,
    ProposalNotFoundError,
    UserNotAllowed,
    UserNotFoundError,
)
from rizana.api.schemas.user import UserQuery


class ChatController:
    """
    Handles chat-related operations such as getting conversations, sending messages, creating proposals, accepting and refusing proposals.
    """

    def __init__(
        self,
        db: AsyncSession,
        user_controller: UserController,
        item_controller: ItemController,
        order_controller: OrderController,
    ):
        """
        Initializes the ChatController with the necessary dependencies.

        Args:
            db (AsyncSession): The database session to use for operations.
            user_controller (UserController): The controller for user-related operations.
            item_controller (ItemController): The controller for item-related operations.
            order_controller (OrderController): The controller for order-related operations.
        """
        self.db = db
        self.user_controller = user_controller
        self.item_controller = item_controller
        self.order_controller = order_controller

    async def get_conversation(
        self, buyer_id: UUID, seller_id: UUID, item_id: UUID
    ) -> Conversation:
        """
        Retrieves a conversation based on the buyer, seller, and item IDs.

        Args:
            buyer_id (UUID): The ID of the buyer.
            seller_id (UUID): The ID of the seller.
            item_id (UUID): The ID of the item.

        Returns:
            Conversation: The conversation object if found, otherwise None.
        """
        try:
            conversation = (
                await self.db.exec(
                    select(Conversation).where(
                        (Conversation.buyer_id == buyer_id)
                        & (Conversation.seller_id == seller_id)
                        & (Conversation.item_id == item_id)
                    )
                )
            ).one()
        except sqlalchemy.exc.NoResultFound:
            raise ConversationNotFoundErrorByUsers(
                buyer_id=buyer_id, seller_id=seller_id, item_id=item_id
            )

        return conversation

    async def get_conversation_by_id(self, conversation_id: UUID) -> Conversation:
        """
        Retrieves a conversation by its ID.

        Args:
            conversation_id (UUID): The ID of the conversation.

        Returns:
            Conversation: The conversation object if found, otherwise raises ConversationNotFoundError.
        """
        conversation = await self.db.get(Conversation, conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id=conversation_id)
        return conversation

    async def create_conversation(
        self, buyer_id: UUID, seller_id: UUID, item_id: UUID
    ) -> Conversation:
        """
        Creates a new conversation between a buyer and a seller for a specific item.

        Args:
            buyer_id (UUID): The ID of the buyer.
            seller_id (UUID): The ID of the seller.
            item_id (UUID): The ID of the item.

        Returns:
            Conversation: The newly created conversation object.
        """
        try:
            conversation = Conversation(
                buyer_id=buyer_id, seller_id=seller_id, item_id=item_id
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
        except sqlalchemy.exc.IntegrityError as e:
            await self.db.rollback()
            raise e

        return conversation

    async def send_message(
        self, sender_id: UUID, message_create: MessageCreate
    ) -> Conversation:
        """
        Sends a message from a sender to a receiver within a conversation.

        Args:
            sender_id (UUID): The ID of the sender.
            message_create (MessageCreate): The message to be sent.

        Returns:
            Conversation: The conversation object after sending the message.
        """
        is_new_conversation = False
        try:
            sender = await self.user_controller.get_user(UserQuery(user_id=sender_id))
            receiver = await self.user_controller.get_user(
                UserQuery(user_id=message_create.receiver_id)
            )
        except UserNotFoundError as e:
            raise e
        print("Conversation ID: ", message_create.conversation_id)
        if message_create.conversation_id:
            print("Getting conversation by ID")
            conversation = await self.get_conversation_by_id(
                message_create.conversation_id
            )
        else:
            item = await self.item_controller.get_item(message_create.item_id)  # type: ignore
            conversation = await self.create_conversation(
                buyer_id=sender_id if sender_id != item.user_id else receiver.id,
                seller_id=item.user_id,
                item_id=message_create.item_id,  # type: ignore
            )
            is_new_conversation = True
        # try:
        #     conversation = await self.get_conversation_by_id(
        #         message_create.conversation_id
        #     )
        # except ConversationNotFoundError as e:
        #     if message_create.item_id is None:
        #         raise e
        #     item = await self.item_controller.get_item(message_create.item_id)
        #     conversation = await self.create_conversation(
        #         buyer_id=sender.id if sender.id != item.user_id else receiver.id,
        #         seller_id=item.user_id,
        #         item_id=message_create.item_id,
        #     )
        #     is_new_conversation = True

        if is_new_conversation is False:
            conversation.updated_at = datetime.now()
            self.db.add(conversation)

        new_message = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            conversation_id=conversation.id,
            message=message_create.message,
        )
        self.db.add(new_message)
        await self.db.commit()
        await self.db.refresh(new_message)
        await self.db.refresh(conversation)
        return conversation

    async def create_proposal(
        self, sender_id: UUID, proposal_create: ProposalCreate
    ) -> Conversation:
        """
        Creates a proposal from a sender to a receiver within a conversation.

        Args:
            sender_id (UUID): The ID of the sender.
            proposal_create (ProposalCreate): The proposal to be created.

        Returns:
            Conversation: The conversation object after creating the proposal.
        """
        is_new_conversation = False
        sender = await self.user_controller.get_user(UserQuery(user_id=sender_id))
        receiver = await self.user_controller.get_user(
            UserQuery(user_id=proposal_create.receiver_id)
        )
        try:
            conversation = await self.get_conversation_by_id(
                proposal_create.conversation_id  # type: ignore
            )
        except ConversationNotFoundError as e:
            if proposal_create.item_id is None:
                raise e
            item = await self.item_controller.get_item(proposal_create.item_id)
            conversation = await self.create_conversation(
                buyer_id=sender_id if sender_id != item.user_id else receiver.id,
                seller_id=item.user_id,
                item_id=proposal_create.item_id,
            )
            is_new_conversation = True

        if is_new_conversation is False:
            conversation.updated_at = datetime.now()
            self.db.add(conversation)

        new_proposal = Proposal(
            proposed_price=proposal_create.proposed_price,
            sender_id=sender.id,
            receiver_id=(
                conversation.seller_id
                if sender.id != conversation.seller_id
                else conversation.buyer_id
            ),
            conversation_id=conversation.id,
        )
        self.db.add(new_proposal)
        await self.db.commit()
        await self.db.refresh(new_proposal)
        await self.db.refresh(conversation)
        return conversation

    async def accept_proposal(self, proposal_id: UUID, user_id: UUID) -> Conversation:
        """
        Accepts a proposal and creates an order.

        Args:
            proposal_id (UUID): The ID of the proposal.
            user_id (UUID): The ID of the user accepting the proposal.

        Returns:
            Conversation: The conversation object after accepting the proposal.
        """
        proposal = (
            await self.db.exec(select(Proposal).where(Proposal.id == proposal_id))
        ).first()
        if not proposal:
            raise ProposalNotFoundError(proposal_id=proposal_id)

        conversation = await self.db.get(Conversation, proposal.conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id=proposal.conversation_id)

        if proposal.sender_id == user_id:
            raise UserNotAllowed(uuid=user_id, action="accept your own proposal")

        if conversation.seller_id != user_id and conversation.buyer_id != user_id:
            raise UserNotAllowed(
                uuid=user_id, action="accept a proposal that is not yours"
            )

        proposal.status = ProposalStatus.ACCEPTED
        conversation.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def refuse_proposal(self, proposal_id: UUID, user_id: UUID) -> Conversation:
        """
        Refuses a proposal.

        Args:
            proposal_id (UUID): The ID of the proposal.
            user_id (UUID): The ID of the user refusing the proposal.

        Returns:
            Conversation: The conversation object after refusing the proposal.
        """
        proposal = (
            await self.db.exec(select(Proposal).where(Proposal.id == proposal_id))
        ).first()
        if not proposal:
            raise ProposalNotFoundError(proposal_id=proposal_id)

        conversation = await self.db.get(Conversation, proposal.conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id=proposal.conversation_id)

        if conversation.seller_id != user_id and conversation.buyer_id != user_id:
            raise UserNotAllowed(
                uuid=user_id, action="refuse a proposal that is not yours"
            )

        proposal.status = ProposalStatus.REJECTED
        conversation.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(proposal)
        await self.db.refresh(conversation)
        return conversation

    async def _get_conversation(self, conversation_id: UUID) -> Conversation:
        """
        Retrieves a conversation by its ID, used internally.

        Args:
            conversation_id (UUID): The ID of the conversation.

        Returns:
            Conversation: The conversation object if found, otherwise raises ConversationNotFoundError.
        """
        conversation = await self.db.get(Conversation, conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id=conversation_id)
        return conversation
