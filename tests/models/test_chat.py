from uuid import uuid4

import pytest
from faker import Faker

from rizana.api.schemas.chat import MessageCreate, ProposalCreate


@pytest.mark.asyncio
async def test_message_create_valid(faker: Faker):
    conversation_id = uuid4()
    receiver_id = uuid4()
    message = faker.sentence()
    message_create = MessageCreate(
        conversation_id=conversation_id,
        receiver_id=receiver_id,
        message=message,
    )
    assert message_create.conversation_id == conversation_id
    assert message_create.receiver_id == receiver_id
    assert message_create.message == message


@pytest.mark.asyncio
async def test_message_create_invalid_message(faker: Faker):
    with pytest.raises(ValueError):
        MessageCreate(
            conversation_id=uuid4(),
            receiver_id=uuid4(),
            message="",  # Empty message
        )


@pytest.mark.asyncio
async def test_proposal_create_valid(faker: Faker):
    item_id = uuid4()
    proposed_price = faker.pyfloat(positive=True, max_value=1000, right_digits=2)
    conversation_id = uuid4()
    receiver_id = uuid4()
    proposal_create = ProposalCreate(
        proposed_price=proposed_price,
        receiver_id=receiver_id,
        item_id=item_id,
        conversation_id=conversation_id,
    )
    assert proposal_create.item_id == item_id
    assert proposal_create.proposed_price == proposed_price
    assert proposal_create.conversation_id == conversation_id


@pytest.mark.asyncio
async def test_proposal_create_invalid_price(faker: Faker):
    with pytest.raises(ValueError):
        ProposalCreate(
            item_id=uuid4(),
            proposed_price=-10.0,  # Negative price
            conversation_id=uuid4(),
            receiver_id=uuid4(),
        )
