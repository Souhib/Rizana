from uuid import UUID

import pytest
from faker import Faker

from rizana.api.controllers.item import ItemController
from rizana.api.controllers.user import UserController
from rizana.api.models.table import Category, Item
from rizana.api.schemas.error import (
    CategoryAlreadyExist,
    CategoryDoesNotExist,
    ItemDoesNotExist,
    ItemsDependsOnCategory,
    UserNotAllowed,
)
from rizana.api.schemas.item import CategoryCreate, ItemCreate
from tests.conftest import create_category, create_user


@pytest.mark.asyncio
async def test_create_item_without_images_and_categories(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[],
        categories=[],
    )
    item = await item_controller.create_item(item_create, user.id)
    assert isinstance(item, Item)
    assert item.title == item_create.title
    assert item.user_id == user.id


@pytest.mark.asyncio
async def test_create_item_category_not_exist(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[faker.word()],
    )
    user = await create_user(user_controller, faker)
    with pytest.raises(CategoryDoesNotExist):
        await item_controller.create_item(item_create, user.id)


@pytest.mark.asyncio
async def test_get_item_without_images_and_categories(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[],
        categories=[],
    )
    created_item = await item_controller.create_item(item_create, user.id)
    retrieved_item = await item_controller.get_item(created_item.id)
    assert retrieved_item.id == created_item.id
    assert retrieved_item.title == item_create.title
    assert retrieved_item.description == item_create.description
    assert retrieved_item.price == item_create.price


@pytest.mark.asyncio
async def test_get_item_with_images_and_categories(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    category = await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[category.name],
    )
    created_item = await item_controller.create_item(item_create, user.id)
    retrieved_item = await item_controller.get_item(created_item.id)
    assert retrieved_item.id == created_item.id
    assert retrieved_item.title == item_create.title
    assert retrieved_item.description == item_create.description
    assert retrieved_item.price == item_create.price
    for image in item_create.images:
        assert image in [img.url for img in retrieved_item.images]
    assert category.name in [cat.name for cat in retrieved_item.categories]


@pytest.mark.asyncio
async def test_get_item_not_found(item_controller: ItemController):
    with pytest.raises(ItemDoesNotExist):
        await item_controller.get_item(UUID("00000000-0000-0000-0000-000000000000"))


@pytest.mark.asyncio
async def test_delete_item_without_images_and_categories(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[],
        categories=[],
    )
    created_item = await item_controller.create_item(item_create, user.id)
    await item_controller.delete_item(created_item.id, user.id)
    with pytest.raises(ItemDoesNotExist):
        await item_controller.get_item(created_item.id)


@pytest.mark.asyncio
async def test_delete_item_with_images_and_categories(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    category = await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[category.name],
    )
    created_item = await item_controller.create_item(item_create, user.id)
    await item_controller.delete_item(created_item.id, user.id)
    with pytest.raises(ItemDoesNotExist):
        await item_controller.get_item(created_item.id)


@pytest.mark.asyncio
async def test_delete_item_not_owner(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    category = await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[category.name],
    )
    created_item = await item_controller.create_item(item_create, user.id)
    other_user = await create_user(user_controller, faker, email="other@example.com")
    with pytest.raises(UserNotAllowed):
        await item_controller.delete_item(created_item.id, other_user.id)


@pytest.mark.asyncio
async def test_create_category_success(item_controller: ItemController, faker: Faker):
    category_create = CategoryCreate(name=faker.word(), description=faker.sentence())
    category = await item_controller.create_category(category_create)
    assert isinstance(category, Category)
    assert category.name == category_create.name


@pytest.mark.asyncio
async def test_create_category_duplicate(item_controller: ItemController, faker: Faker):
    category_create = CategoryCreate(name=faker.word(), description=faker.sentence())
    await item_controller.create_category(category_create)
    with pytest.raises(CategoryAlreadyExist):
        await item_controller.create_category(category_create)


@pytest.mark.asyncio
async def test_delete_category_success(item_controller: ItemController, faker: Faker):
    category_create = CategoryCreate(name=faker.word(), description=faker.sentence())
    category = await item_controller.create_category(category_create)
    await item_controller.delete_category(category.name)
    with pytest.raises(CategoryDoesNotExist):
        await item_controller.get_category(category.name)


@pytest.mark.asyncio
async def test_delete_category_with_items(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    category = await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[category.name],
    )
    user = await create_user(user_controller, faker)
    await item_controller.create_item(item_create, user.id)
    with pytest.raises(ItemsDependsOnCategory):
        await item_controller.delete_category(category.name)


@pytest.mark.asyncio
async def test_create_item_with_multiple_categories(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    category1 = await create_category(item_controller, faker)
    category2 = await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[category1.name, category2.name],
    )
    item = await item_controller.create_item(item_create, user.id)
    assert isinstance(item, Item)
    assert len(item.categories) == 2
    assert category1.name in [cat.name for cat in item.categories]
    assert category2.name in [cat.name for cat in item.categories]


@pytest.mark.asyncio
async def test_create_item_without_categories(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[],
    )
    item = await item_controller.create_item(item_create, user.id)
    assert isinstance(item, Item)
    assert len(item.categories) == 0


@pytest.mark.asyncio
async def test_get_user_items(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    category = await create_category(item_controller, faker)
    items_count = faker.random_int(min=1, max=5)
    for _ in range(items_count):
        item_create = ItemCreate(
            title=faker.word(),
            description=faker.sentence(),
            price=faker.random_int(min=1, max=1000) / 100,
            images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
            categories=[category.name],
        )
        await item_controller.create_item(item_create, user.id)

    user_items = await item_controller.get_user_items(user.id)
    assert len(user_items) == items_count
    assert all(isinstance(item, Item) for item in user_items)


@pytest.mark.asyncio
async def test_get_category(item_controller: ItemController, faker: Faker):
    category_create = CategoryCreate(name=faker.word(), description=faker.sentence())
    created_category = await item_controller.create_category(category_create)
    retrieved_category = await item_controller.get_category(created_category.name)
    assert isinstance(retrieved_category, Category)
    assert retrieved_category.name == created_category.name
    assert retrieved_category.description == created_category.description


@pytest.mark.asyncio
async def test_get_category_not_found(item_controller: ItemController, faker: Faker):
    with pytest.raises(CategoryDoesNotExist):
        await item_controller.get_category(faker.word())


@pytest.mark.asyncio
async def test_create_item_without_images(
    user_controller: UserController, item_controller: ItemController, faker: Faker
):
    user = await create_user(user_controller, faker)
    category = await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[],  # Empty list of images
        categories=[category.name],
    )
    item = await item_controller.create_item(item_create, user.id)
    assert isinstance(item, Item)
    assert len(item.images) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_category(
    item_controller: ItemController, faker: Faker
):
    with pytest.raises(CategoryDoesNotExist):
        await item_controller.delete_category(faker.word())
