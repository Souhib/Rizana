import pytest
from faker import Faker

from rizana.api.schemas.item import CategoryCreate, ItemCreate


@pytest.mark.asyncio
async def test_create_item_with_invalid_price(faker: Faker):
    with pytest.raises(ValueError):
        ItemCreate(
            title=faker.word(),
            description=faker.sentence(),
            price=-10,  # Invalid negative price
            images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
            categories=[faker.word()],
        )


@pytest.mark.asyncio
async def test_create_item_with_long_title(faker: Faker):
    with pytest.raises(ValueError):
        ItemCreate(
            title=faker.pystr(
                min_chars=101, max_chars=110
            ),  # Title longer than 100 characters
            description=faker.sentence(),
            price=faker.random_int(min=1, max=1000) / 100,
            images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
            categories=[faker.word()],
        )


@pytest.mark.asyncio
async def test_create_item_with_long_description(faker: Faker):
    with pytest.raises(ValueError):
        ItemCreate(
            title=faker.word(),
            description=faker.pystr(
                min_chars=1001, max_chars=1010
            ),  # Description longer than 1000 characters
            price=faker.random_int(min=1, max=1000) / 100,
            images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
            categories=[faker.word()],
        )


@pytest.mark.asyncio
async def test_create_category_with_long_name(faker: Faker):
    with pytest.raises(ValueError):
        CategoryCreate(
            name=faker.pystr(
                min_chars=51, max_chars=60
            ),  # Name longer than 50 characters
            description=faker.sentence(),
        )


@pytest.mark.asyncio
async def test_create_category_with_long_description(faker: Faker):
    with pytest.raises(ValueError):
        CategoryCreate(
            name=faker.word(),
            description=faker.pystr(
                min_chars=256, max_chars=260
            ),  # Description longer than 255 characters
        )
