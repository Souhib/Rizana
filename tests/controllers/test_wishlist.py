from uuid import UUID

import pytest
from faker import Faker

from rizana.api.controllers.item import ItemController
from rizana.api.controllers.user import UserController
from rizana.api.controllers.wishlist import WishlistController
from rizana.api.models.table import Item, Wish
from rizana.api.schemas.error import (ItemAlreadyInWishList, ItemDoesNotExist,
                                      UserCantAddHisOwnItemToWishlist,
                                      WishDoesNotExists)
from rizana.api.schemas.wishlist import WishCreate
from tests.conftest import create_item, create_user


@pytest.mark.asyncio
async def test_create_wish_success(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    user = await create_user(user_controller, faker)
    user2 = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=user.id)
    wish_create = WishCreate(item_id=item.id, user_id=user2.id)
    wish = await wishlist_controller.create_wish(wish_create, user2)
    assert isinstance(wish, Wish)
    assert wish.user_id == user2.id
    assert wish.item_id == item.id


@pytest.mark.asyncio
async def test_create_wish_item_already_in_wishlist(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    user = await create_user(user_controller, faker)
    user2 = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=user.id)
    wish_create = WishCreate(item_id=item.id, user_id=user2.id)
    await wishlist_controller.create_wish(wish_create, user2)
    with pytest.raises(ItemAlreadyInWishList):
        await wishlist_controller.create_wish(wish_create, user2)


@pytest.mark.asyncio
async def test_create_wish_item_does_not_exist(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    faker: Faker,
):
    user = await create_user(user_controller, faker)
    wish_create = WishCreate(
        item_id=UUID("00000000-0000-0000-0000-000000000000"), user_id=user.id
    )
    with pytest.raises(ItemDoesNotExist):
        await wishlist_controller.create_wish(wish_create, user)


@pytest.mark.asyncio
async def test_create_wish_user_own_item(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    user = await create_user(user_controller, faker)
    item = await create_item(item_controller, faker, user_id=user.id)
    wish_create = WishCreate(item_id=item.id, user_id=user.id)
    with pytest.raises(UserCantAddHisOwnItemToWishlist):
        await wishlist_controller.create_wish(wish_create, user)


@pytest.mark.asyncio
async def test_remove_wish_success(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    user = await create_user(user_controller, faker)
    user2 = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=user.id)
    wish_create = WishCreate(item_id=item.id, user_id=user2.id)
    wish = await wishlist_controller.create_wish(wish_create, user2)
    await wishlist_controller.remove_wish(wish.item_id, user2.id)
    with pytest.raises(WishDoesNotExists):
        await wishlist_controller.remove_wish(wish.item_id, user2.id)


@pytest.mark.asyncio
async def test_remove_wish_not_exists(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    faker: Faker,
):
    user = await create_user(user_controller, faker)
    with pytest.raises(WishDoesNotExists):
        await wishlist_controller.remove_wish(
            UUID("00000000-0000-0000-0000-000000000000"), user.id
        )


@pytest.mark.asyncio
async def test_get_wishlist(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    user = await create_user(user_controller, faker)
    user2 = await create_user(user_controller, faker, email=faker.email())
    items = [
        await create_item(item_controller, faker, user_id=user.id) for _ in range(3)
    ]
    for item in items:
        wish_create = WishCreate(item_id=item.id, user_id=user2.id)
        await wishlist_controller.create_wish(wish_create, user2)

    wishlist = await wishlist_controller.get_wishlist(user2.id)
    assert len(wishlist) == 3
    assert all(isinstance(item, Item) for item in wishlist)
    assert all(item.id in [i.id for i in items] for item in wishlist)
