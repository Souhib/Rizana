from datetime import datetime
from uuid import uuid4

import freezegun
import pytest
from faker import Faker

from rizana.api.controllers.chat import ChatController
from rizana.api.controllers.item import ItemController
from rizana.api.controllers.user import UserController
from rizana.api.models.table import Conversation
from rizana.api.schemas.chat import MessageCreate, ProposalCreate
from rizana.api.schemas.error import (ConversationNotFoundError,
                                      ConversationNotFoundErrorByUsers,
                                      ProposalNotFoundError, UserNotAllowed,
                                      UserNotFoundError)
from tests.conftest import create_item, create_user


@pytest.mark.asyncio
async def test_create_conversation_success(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    assert isinstance(conversation, Conversation)
    assert conversation.buyer_id == buyer.id
    assert conversation.seller_id == seller.id
    assert conversation.item_id == item.id


@pytest.mark.asyncio
async def test_get_conversation_success(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    retrieved_conversation = await chat_controller.get_conversation(
        buyer.id, seller.id, item.id
    )

    assert retrieved_conversation
    assert conversation.id == retrieved_conversation.id
    assert conversation.buyer_id == retrieved_conversation.buyer_id
    assert conversation.seller_id == retrieved_conversation.seller_id
    assert conversation.item_id == retrieved_conversation.item_id
    assert conversation.created_at == retrieved_conversation.created_at
    assert conversation.updated_at == retrieved_conversation.updated_at


@pytest.mark.asyncio
async def test_send_message_success_with_conversation(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    message_create = MessageCreate(
        conversation_id=conversation.id, receiver_id=seller.id, message=faker.sentence()
    )
    conversation = await chat_controller.send_message(buyer.id, message_create)
    messages = conversation.messages
    assert isinstance(conversation, Conversation)
    assert messages[0].sender_id == buyer.id
    assert messages[0].receiver_id == seller.id
    assert messages[0].conversation_id == conversation.id


@pytest.mark.asyncio
async def test_send_message_success_without_conversation(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    message_create = MessageCreate(
        receiver_id=seller.id, item_id=item.id, message=faker.sentence()
    )
    conversation = await chat_controller.send_message(buyer.id, message_create)
    messages = conversation.messages
    assert isinstance(conversation, Conversation)
    assert messages[0].sender_id == buyer.id
    assert messages[0].receiver_id == seller.id
    assert messages[0].conversation_id == conversation.id


@pytest.mark.asyncio
async def test_create_proposal_success_buyer_send_proposal_without_conversation_created(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        receiver_id=seller.id,
        item_id=item.id,
    )
    conversation = await chat_controller.create_proposal(buyer.id, proposal_create)
    assert isinstance(conversation, Conversation)
    assert conversation.proposals[0].sender_id == buyer.id
    assert conversation.proposals[0].receiver_id == seller.id
    assert conversation.proposals[0].proposed_price == proposal_create.proposed_price
    assert conversation.proposals[0].status == "pending"


@pytest.mark.asyncio
async def test_create_proposal_success_seller_send_proposal_conversation_created(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        receiver_id=buyer.id,
        item_id=item.id,
    )
    conversation = await chat_controller.create_proposal(seller.id, proposal_create)
    assert isinstance(conversation, Conversation)
    assert conversation.proposals[0].sender_id == seller.id
    assert conversation.proposals[0].receiver_id == buyer.id
    assert conversation.proposals[0].proposed_price == proposal_create.proposed_price
    assert conversation.proposals[0].status == "pending"


@pytest.mark.asyncio
async def test_create_proposal_success_buyer_send_proposal_conversation_created(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        receiver_id=seller.id,
        conversation_id=conversation.id,
    )
    conversation = await chat_controller.create_proposal(buyer.id, proposal_create)
    assert isinstance(conversation, Conversation)
    assert conversation.proposals[0].sender_id == buyer.id
    assert conversation.proposals[0].receiver_id == seller.id
    assert conversation.proposals[0].proposed_price == proposal_create.proposed_price
    assert conversation.proposals[0].status == "pending"


@pytest.mark.asyncio
@freezegun.freeze_time("2023-01-01")
async def test_accept_proposal_success(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        item_id=item.id,
        receiver_id=seller.id,
    )
    conversation = await chat_controller.create_proposal(buyer.id, proposal_create)

    with freezegun.freeze_time("2023-01-02"):
        conversation = await chat_controller.accept_proposal(
            conversation.proposals[0].id, seller.id
        )

    assert conversation.proposals[0].status == "accepted"
    assert conversation.updated_at == datetime(2023, 1, 2)


@pytest.mark.asyncio
async def test_accept_proposal_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    with pytest.raises(ProposalNotFoundError):
        await chat_controller.accept_proposal(uuid4(), buyer.id)


@pytest.mark.asyncio
async def test_accept_your_own_proposal(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    seller = await create_user(user_controller, faker)
    buyer = await create_user(user_controller, faker)
    item = await create_item(item_controller, faker, user_id=seller.id)
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        receiver_id=buyer.id,
        item_id=item.id,
    )
    conversation = await chat_controller.create_proposal(buyer.id, proposal_create)
    with pytest.raises(UserNotAllowed):
        await chat_controller.accept_proposal(conversation.proposals[0].id, buyer.id)


@pytest.mark.asyncio
@freezegun.freeze_time("2023-01-01")
async def test_accept_proposal_that_is_someone_else(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    another_seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        item_id=item.id,
        receiver_id=seller.id,
    )
    conversation = await chat_controller.create_proposal(buyer.id, proposal_create)
    with pytest.raises(UserNotAllowed):
        await chat_controller.accept_proposal(
            conversation.proposals[0].id, another_seller.id
        )


@pytest.mark.asyncio
@freezegun.freeze_time("2023-01-01")
async def test_refuse_proposal_success(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        item_id=item.id,
        receiver_id=seller.id,
    )
    conversation = await chat_controller.create_proposal(buyer.id, proposal_create)

    with freezegun.freeze_time("2023-01-02"):
        conversation = await chat_controller.refuse_proposal(
            conversation.proposals[0].id, seller.id
        )

    assert conversation.proposals[0].status == "rejected"
    assert conversation.updated_at == datetime(2023, 1, 2)


@pytest.mark.asyncio
async def test_get_conversation_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    with pytest.raises(ConversationNotFoundErrorByUsers):
        await chat_controller.get_conversation(buyer.id, seller.id, uuid4())


@pytest.mark.asyncio
async def test_send_message_conversation_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    message_create = MessageCreate(
        conversation_id=uuid4(), receiver_id=seller.id, message=faker.sentence()
    )
    with pytest.raises(ConversationNotFoundError):
        await chat_controller.send_message(buyer.id, message_create)


@pytest.mark.asyncio
async def test_send_message_sender_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    message_create = MessageCreate(
        conversation_id=conversation.id, receiver_id=seller.id, message=faker.sentence()
    )
    with pytest.raises(UserNotFoundError):
        await chat_controller.send_message(uuid4(), message_create)


@pytest.mark.asyncio
async def test_send_message_receiver_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    message_create = MessageCreate(
        conversation_id=conversation.id, receiver_id=uuid4(), message=faker.sentence()
    )
    with pytest.raises(UserNotFoundError):
        await chat_controller.send_message(seller.id, message_create)


@pytest.mark.asyncio
async def test_create_proposal_conversation_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        receiver_id=seller.id,
        conversation_id=uuid4(),
    )
    with pytest.raises(ConversationNotFoundError):
        await chat_controller.create_proposal(buyer.id, proposal_create)


@pytest.mark.asyncio
async def test_create_proposal_sender_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        receiver_id=seller.id,
        conversation_id=conversation.id,
    )
    with pytest.raises(UserNotFoundError):
        await chat_controller.create_proposal(uuid4(), proposal_create)


@pytest.mark.asyncio
async def test_create_proposal_receiver_not_found(
    chat_controller: ChatController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)
    conversation = await chat_controller.create_conversation(
        buyer_id=buyer.id, seller_id=seller.id, item_id=item.id
    )
    proposal_create = ProposalCreate(
        proposed_price=faker.pyfloat(positive=True, max_value=1000, right_digits=2),
        receiver_id=uuid4(),
        conversation_id=conversation.id,
    )
    with pytest.raises(UserNotFoundError):
        await chat_controller.create_proposal(seller.id, proposal_create)
