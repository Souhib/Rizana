import pytest
from faker import Faker

from rizana.api.schemas.user import UserCreate


def generate_random_emirate_id(faker: Faker):
    return f"784-{faker.random_int(min=1000, max=9999)}-{faker.random_int(min=1000000, max=9999999)}-{faker.random_int(min=1, max=2)}"


@pytest.mark.asyncio
async def test_create_user_invalid_emirate_id(faker: Faker):
    with pytest.raises(ValueError, match="Format of Emirate ID is not correct"):
        UserCreate(
            username=faker.user_name(),
            email=faker.email(),
            password=faker.password(),
            emirate_id="invalid-id",
            country="ARE",
        )


@pytest.mark.asyncio
async def test_create_user_missing_emirate_id(faker: Faker):
    with pytest.raises(ValueError, match="Emirate ID is required for users from UAE"):
        UserCreate(
            username=faker.user_name(),
            email=faker.email(),
            password=faker.password(),
            country="ARE",
        )


@pytest.mark.asyncio
async def test_create_user_with_invalid_country_code(faker: Faker):
    with pytest.raises(
        ValueError, match="Country must be a valid 3-letter country code"
    ):
        UserCreate(
            username=faker.user_name(),
            email=faker.email(),
            password=faker.password(),
            country="XYZ",
        )


@pytest.mark.asyncio
async def test_create_user_with_invalid_email(faker: Faker):
    with pytest.raises(ValueError):
        UserCreate(
            username=faker.user_name(),
            email="invalid_email",
            password=faker.password(),
            emirate_id=generate_random_emirate_id(faker),
            country="ARE",
        )
