import random
from datetime import timedelta
from uuid import UUID

import pytest
from faker import Faker
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.user import UserController
from rizana.api.models.table import User
from rizana.api.schemas.error import (
    EmailNotRecognizedError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserIsInactive,
    UserNotFoundError,
    WrongPasswordError,
)
from rizana.api.schemas.user import UserCreate, UserQuery


async def activate_user(user_controller: UserController, user_id: UUID):
    email_activation_key = await user_controller._get_latest_active_activation_key(
        user_id=user_id
    )
    await user_controller.activate_user(user_id=user_id, token=email_activation_key)


def generate_random_emirate_id():
    return f"784-{random.randint(1000, 9999)}-{random.randint(1000000, 9999999)}-{random.randint(1, 2)}"


@pytest.fixture
def user_create(faker):
    return UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
        emirate_id=generate_random_emirate_id(),
        country="ARE",
    )


@pytest.mark.asyncio
async def test_creates_new_user_with_valid_input(
    user_controller: UserController, session: AsyncSession, faker: Faker
):
    # Arrange
    user_create = UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        emirate_id=generate_random_emirate_id(),
        password=faker.password(),
    )

    # Act
    result = await user_controller.create_user(user_create)
    db_user = (await session.exec(select(User).where(User.id == result.id))).one()

    # Assert
    assert db_user is not None
    assert db_user.username == user_create.username
    assert db_user.email == user_create.email
    assert db_user.emirate_id == user_create.emirate_id
    assert user_controller.ph.verify(db_user.password, user_create.password)
    assert db_user.id == result.id
    assert db_user.created_at is not None
    assert db_user.is_active is False
    assert db_user.is_admin is True
    assert db_user.items == []
    assert db_user.orders == []
    assert db_user.sales == []
    assert db_user.reviews == []
    assert db_user.addresses == []
    assert db_user.payment_methods == []
    assert db_user.wishlist == []
    assert db_user.messages_sent == []
    assert db_user.messages_received == []
    assert db_user.conversations_as_buyer == []
    assert db_user.conversations_as_seller == []
    assert db_user.favorites == []
    assert db_user.feedback == []
    assert db_user.activity_logs == []
    assert db_user.charity_contributions == []


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    user_controller: UserController, session: AsyncSession, faker: Faker
):
    user_create = UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        emirate_id=generate_random_emirate_id(),
        password=faker.password(),
    )
    await user_controller.create_user(user_create)
    with pytest.raises(UserAlreadyExistsError):
        await user_controller.create_user(user_create)


@pytest.mark.asyncio
async def test_get_user_by_id(user_controller: UserController, user_create: UserCreate):
    created_user = await user_controller.create_user(user_create)
    await activate_user(user_controller, created_user.id)
    retrieved_user = await user_controller.get_user(UserQuery(user_id=created_user.id))
    assert retrieved_user.id == created_user.id


@pytest.mark.asyncio
async def test_get_user_not_found(user_controller: UserController):
    with pytest.raises(UserNotFoundError):
        await user_controller.get_user(
            UserQuery(user_id=UUID("00000000-0000-0000-0000-000000000000"))
        )


@pytest.mark.asyncio
async def test_login_user_success(
    user_controller: UserController, user_create: UserCreate
):
    user = await user_controller.create_user(user_create)
    form_data = OAuth2PasswordRequestForm(
        username=user_create.email, password=user_create.password
    )
    await activate_user(user_controller, user.id)
    login_result = await user_controller.login_user(form_data)
    assert "access_token" in login_result
    assert login_result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_wrong_password(
    user_controller: UserController, user_create: UserCreate
):
    user = await user_controller.create_user(user_create)
    await activate_user(user_controller, user.id)
    form_data = OAuth2PasswordRequestForm(
        username=user_create.email, password="wrongpassword"
    )
    with pytest.raises(WrongPasswordError):
        await user_controller.login_user(form_data)


@pytest.mark.asyncio
async def test_login_user_email_not_recognized(user_controller: UserController):
    form_data = OAuth2PasswordRequestForm(
        username="nonexistent@example.com", password="testpassword"
    )
    with pytest.raises(EmailNotRecognizedError):
        await user_controller.login_user(form_data)


@pytest.mark.asyncio
async def test_create_access_token(user_controller: UserController):
    data = {"sub": "test@example.com"}
    token = await user_controller.create_access_token(data)
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_get_current_user_token_valid(user_controller: UserController):
    data = {"sub": "test@example.com"}
    token = await user_controller.create_access_token(data)
    email = await user_controller.get_current_user_token(token)
    assert email == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_token_invalid(user_controller: UserController):
    with pytest.raises(InvalidTokenError):
        await user_controller.get_current_user_token("invalid_token")


@pytest.mark.asyncio
async def test_create_user_with_non_uae_country(
    user_controller: UserController, faker: Faker
):
    user_create = UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
        country="USA",
    )
    result = await user_controller.create_user(user_create)
    assert result.country == "USA"
    assert result.emirate_id is None


@pytest.mark.asyncio
async def test_get_user_by_username(
    user_controller: UserController, user_create: UserCreate
):
    created_user = await user_controller.create_user(user_create)
    await activate_user(user_controller, created_user.id)
    retrieved_user = await user_controller.get_user(
        UserQuery(username=created_user.username)
    )
    assert retrieved_user.username == created_user.username


@pytest.mark.asyncio
async def test_get_user_by_email(
    user_controller: UserController, user_create: UserCreate
):
    created_user = await user_controller.create_user(user_create)
    await activate_user(user_controller, created_user.id)
    retrieved_user = await user_controller.get_user(UserQuery(email=created_user.email))
    assert retrieved_user.email == created_user.email


@pytest.mark.asyncio
async def test_get_user_by_emirate_id(
    user_controller: UserController, user_create: UserCreate
):
    created_user = await user_controller.create_user(user_create)
    await activate_user(user_controller, created_user.id)
    retrieved_user = await user_controller.get_user(
        UserQuery(emirate_id=created_user.emirate_id)
    )
    assert retrieved_user.emirate_id == created_user.emirate_id


@pytest.mark.asyncio
async def test_create_access_token_with_expiration(user_controller: UserController):
    data = {"sub": "test@example.com"}
    expires_delta = timedelta(minutes=30)
    token = await user_controller.create_access_token(data, expires_delta)
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_create_access_token_default_expiration(user_controller: UserController):
    data = {"sub": "test@example.com"}
    token = await user_controller.create_access_token(data)
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_get_current_user_token_expired(user_controller: UserController):
    data = {"sub": "test@example.com"}
    token = await user_controller.create_access_token(
        data, expires_delta=timedelta(minutes=-1)
    )

    with pytest.raises(InvalidTokenError):
        await user_controller.get_current_user_token(token)


@pytest.mark.asyncio
async def test_create_user_duplicate_emirate_id(
    user_controller: UserController, faker: Faker
):
    emirate_id = generate_random_emirate_id()
    user_create1 = UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
        emirate_id=emirate_id,
        country="ARE",
    )
    user_create2 = UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
        emirate_id=emirate_id,
        country="ARE",
    )
    await user_controller.create_user(user_create1)
    with pytest.raises(UserAlreadyExistsError):
        await user_controller.create_user(user_create2)


@pytest.mark.asyncio
async def test_login_user_inactive(
    user_controller: UserController, user_create: UserCreate, session: AsyncSession
):
    user = await user_controller.create_user(user_create)
    user.is_active = False
    session.add(user)
    await session.commit()

    form_data = OAuth2PasswordRequestForm(
        username=user_create.email, password=user_create.password
    )
    with pytest.raises(UserIsInactive):
        await user_controller.login_user(form_data)


@pytest.mark.asyncio
async def test_get_user_multiple_criteria(
    user_controller: UserController, user_create: UserCreate
):
    created_user = await user_controller.create_user(user_create)
    await activate_user(user_controller, created_user.id)
    retrieved_user = await user_controller.get_user(
        UserQuery(
            user_id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            emirate_id=created_user.emirate_id,
        )
    )
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == created_user.username
    assert retrieved_user.email == created_user.email
    assert retrieved_user.emirate_id == created_user.emirate_id
