import random
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from faker import Faker
from sqlalchemy import StaticPool
from sqlalchemy.event import listens_for
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.chat import ChatController
from rizana.api.controllers.item import ItemController
from rizana.api.controllers.order import OrderController
from rizana.api.controllers.payment import PaymentController
from rizana.api.controllers.user import UserController
from rizana.api.controllers.wishlist import WishlistController
from rizana.api.models.payment import CardType
from rizana.api.schemas.item import CategoryCreate, ItemCreate
from rizana.api.schemas.payment import PaymentMethodCreate
from rizana.api.schemas.user import UserCreate


@pytest.fixture(name="faker", scope="function")
def get_faker() -> Faker:
    return Faker("ar_AE")


# @pytest.fixture(scope="session")
# def event_loop():
#     try:
#         loop = asyncio.get_running_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#     yield loop
#     loop.close()

# @pytest.fixture
# def event_loop():
#     yield asyncio.get_event_loop()

# def pytest_sessionfinish(session, exitstatus):
#     asyncio.get_event_loop().close()

# @pytest.fixture(name="postgres", scope="session", autouse=True)
# def generate_test_pgsql():
#     with PostgresContainer("postgres:latest") as postgres:
#         postgres.with_env("POSTGRES_USER", "test")
#         postgres.with_env("POSTGRES_PASSWORD", "testpassword")
#         postgres.with_env("POSTGRES_DB", "testdb")
#         yield postgres


@pytest_asyncio.fixture(name="engine", scope="session")
# async def generate_socket_test_pgsql_engine(postgres):
async def generate_socket_test_pgsql_engine():
    # original_url = postgres.get_connection_url()
    # print(f"original_url: {original_url}")
    # async_url = original_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    # print(f"async_url: {async_url}")
    # engine = create_async_engine(async_url)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """
        Sets the foreign keys pragma to ON for SQLite connections.

        This function is a listener for the "connect" event of the engine's sync_engine.
        It sets the foreign keys pragma to ON for each connection to ensure foreign key
        constraints are enforced.

        Args:
            dbapi_connection: The database API connection.
            connection_record: The connection record.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda engine: SQLModel.metadata.create_all(engine, checkfirst=True)
        )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(name="session", scope="function", autouse=True)
async def generate_test_db_session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Generate a test database session.

    This fixture creates an asynchronous SQLAlchemy session for testing purposes.
    The session is created with the given engine and is yielded for use in tests.

    Args:
        engine (AsyncEngine): The SQLAlchemy asynchronous engine.

    Yields:
        AsyncGenerator[AsyncSession, None]: An asynchronous session for database operations.
    """
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest_asyncio.fixture(autouse=True, scope="function")
async def clear_database_and_redis(engine: AsyncEngine, request):
    """Clears the database and Redis after each test function.

    This fixture ensures that the database and Redis are cleared after each test function.
    It checks if the test is a controller test to avoid dropping the database for performance reasons.

    Args:
        engine (AsyncEngine): The SQLAlchemy asynchronous engine.
        request: The pytest request object.

    Yields:
        None
    """
    yield
    if "controller" in str(request.node.fspath):
        async with engine.begin() as conn:
            # await conn.execute(text("PRAGMA foreign_keys = OFF;"))
            await conn.run_sync(SQLModel.metadata.drop_all)
            # await conn.execute(text("PRAGMA foreign_keys = ON;"))
            await conn.run_sync(
                lambda engine: SQLModel.metadata.create_all(engine, checkfirst=True)
            )


def generate_random_emirate_id(faker: Faker) -> str:
    """
    Generate a random Emirates ID.

    Args:
        faker (Faker): An instance of the Faker class to generate random numbers.

    Returns:
        str: A randomly generated Emirates ID in the format '784-XXXX-XXXXXXX-X'.
    """
    return f"784-{faker.random_int(min=1000, max=9999)}-{faker.random_int(min=1000000, max=9999999)}-{faker.random_int(min=1, max=2)}"


@pytest.fixture(scope="function")
def user_create(faker: Faker):
    """
    Fixture to create a user for testing purposes.

    Args:
        faker (Faker): An instance of the Faker library to generate fake data.

    Returns:
        UserCreate: An instance of UserCreate with randomly generated user details.
    """
    return UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
        emirate_id=generate_random_emirate_id(faker),
        country="ARE",
    )


@pytest_asyncio.fixture(name="user_controller", scope="function")
async def get_user_controller(session: AsyncSession) -> UserController:
    """Fixture to provide a UserController instance.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.

    Returns:
        UserController: An instance of UserController.
    """

    async def fake_send_activation_email(*args, **kwargs):
        return True

    patch.object(UserController, "_set_resend_api_key", return_value=None).start()
    patch.object(
        UserController, "_send_activation_email", fake_send_activation_email
    ).start()
    user_controller = UserController(session, "test_secret", "HS256", "FAKE_API_KEY")
    # user_controller.send_activation_email = fake_send_activation_email  # type: ignore
    return user_controller
    # user_controller = UserController(session, "test_secret", "HS256", "FAKE_API_KEY")
    # user_controller.send_activation_email = fake_send_activation_email  # type: ignore
    # return user_controller


@pytest_asyncio.fixture(name="item_controller", scope="function")
async def get_item_controller(session: AsyncSession) -> ItemController:
    """Fixture to provide an ItemController instance.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.

    Returns:
        ItemController: An instance of ItemController.
    """
    return ItemController(session)


@pytest_asyncio.fixture(name="order_controller", scope="function")
async def get_order_controller(
    session: AsyncSession, user_controller: UserController
) -> OrderController:
    """Fixture to provide an OrderController instance.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.
        user_controller (UserController): The controller for user-related operations.

    Returns:
        OrderController: An instance of OrderController.
    """
    return OrderController(session, user_controller)


@pytest_asyncio.fixture(name="wishlist_controller", scope="function")
async def get_wishlist_controller(session: AsyncSession) -> WishlistController:
    """Fixture to provide a WishlistController instance.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.

    Returns:
        WishlistController: An instance of WishlistController.
    """
    return WishlistController(session)


@pytest_asyncio.fixture(name="payment_controller", scope="function")
async def get_payment_controller(session: AsyncSession) -> PaymentController:
    """Fixture to provide a PaymentController instance.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.

    Returns:
        PaymentController: An instance of PaymentController.
    """
    return PaymentController(session)


@pytest_asyncio.fixture(name="chat_controller", scope="function")
async def get_chat_controller(
    session: AsyncSession,
    user_controller: UserController,
    item_controller: ItemController,
    order_controller: OrderController,
) -> ChatController:
    """Fixture to provide a ChatController instance.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.

    Returns:
        ChatController: An instance of ChatController.
    """
    return ChatController(session, user_controller, item_controller, order_controller)


async def create_category(item_controller: ItemController, faker: Faker, **kwargs):
    """Create a category using the ItemController and Faker.

    Args:
        item_controller (ItemController): The controller for item-related operations.
        faker (Faker): An instance of the Faker library for generating fake data.
        **kwargs: Additional keyword arguments to update the category data.

    Returns:
        Category: The newly created category object.
    """
    category_create = CategoryCreate(name=faker.word(), description=faker.sentence())
    category_data = category_create.model_dump()
    category_data.update(kwargs)
    return await item_controller.create_category(CategoryCreate(**category_data))


async def create_user(user_controller: UserController, faker: Faker, **kwargs):
    """Create a user using the UserController and Faker.

    Args:
        user_controller (UserController): The controller for user-related operations.
        faker (Faker): An instance of the Faker library for generating fake data.
        **kwargs: Additional keyword arguments to update the user data.

    Returns:
        User: The newly created user object.
    """
    user_create = UserCreate(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
        emirate_id=generate_random_emirate_id(faker),
        country="ARE",
    )
    active_user = kwargs.pop("active_user", True)
    set_admin = kwargs.pop("set_admin", False)
    user_data = user_create.model_dump()
    user_data.update(kwargs)
    user = await user_controller.create_user(UserCreate(**user_data))
    if active_user:
        activation_key = await user_controller._get_latest_active_activation_key(
            user.id
        )
        user = await user_controller.activate_user(user.id, activation_key)
    if set_admin:
        user = await user_controller.set_user_admin(user.id)
    print("User : ", user)
    return user


async def create_item(item_controller: ItemController, faker: Faker, **kwargs):
    """Create an item using the ItemController and Faker.

    Args:
        item_controller (ItemController): The controller for item-related operations.
        faker (Faker): An instance of the Faker library for generating fake data.
        **kwargs: Additional keyword arguments to update the item data.

    Returns:
        Item: The newly created item object.
    """
    user_id = kwargs.pop("user_id")
    category = await create_category(item_controller, faker)
    item_create = ItemCreate(
        title=faker.word(),
        description=faker.sentence(),
        price=faker.random_int(min=1, max=1000) / 100,
        images=[faker.image_url() for _ in range(faker.random_int(min=1, max=3))],
        categories=[category.name],
    )
    item_data = item_create.model_dump()
    item_data.update(kwargs)
    return await item_controller.create_item(ItemCreate(**item_data), user_id)


async def create_payment(payment_controller: PaymentController, faker: Faker, **kwargs):
    """
    Creates a payment using the PaymentController and Faker.

    Args:
        payment_controller (PaymentController): The controller for payment-related operations.
        faker (Faker): An instance of the Faker library for generating fake data.
        **kwargs: Additional keyword arguments to update the payment data.

    Returns:
        Payment: The newly created payment object.
    """
    user_id = kwargs.pop("user_id")
    payment_create = PaymentMethodCreate(
        card_type=faker.random_element(random.choice(list(CardType))),
        card_number=faker.credit_card_number(),
        expiry_date=faker.credit_card_expire(),
        holder_name=faker.name(),
        cvv=str(faker.random_int(min=100, max=999)),
    )
    payment_data = payment_create.model_dump()
    payment_data.update(kwargs)
    return await payment_controller.create_payment(
        PaymentMethodCreate(**payment_data), user_id
    )
