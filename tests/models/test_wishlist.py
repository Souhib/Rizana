from uuid import uuid4

import pytest
from faker import Faker

from rizana.api.schemas.wishlist import WishCreate


@pytest.mark.asyncio
async def test_wish_create_valid(faker: Faker):
    item_id = uuid4()
    user_id = uuid4()
    wish_create = WishCreate(item_id=item_id, user_id=user_id)
    assert wish_create.item_id == item_id
    assert wish_create.user_id == user_id
