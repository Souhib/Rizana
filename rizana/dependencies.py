from functools import lru_cache

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.chat import ChatController
from rizana.api.controllers.item import ItemController
from rizana.api.controllers.order import OrderController
from rizana.api.controllers.payment import PaymentController
from rizana.api.controllers.user import UserController
from rizana.api.controllers.wishlist import WishlistController
from rizana.api.models.table import User
from rizana.api.schemas.error import UserAccountIsNotActive, UserNotAllowed
from rizana.api.schemas.user import UserQuery
from rizana.api.services.stripe_service import StripeService
from rizana.database import create_app_engine
from rizana.settings import Settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@lru_cache()
def get_settings():
    """
    Returns the application settings.

    This function is a cached function that returns the application settings. It is used to
    inject the settings into various parts of the application.

    Returns:
        Settings: The application settings.
    """
    return Settings()  # type: ignore


async def get_engine():
    """
    Returns the application database engine.

    This function asynchronously creates and returns the application's database engine.

    Returns:
        AsyncEngine: The application's database engine.
    """
    return await create_app_engine()


async def get_session(engine: AsyncEngine = Depends(get_engine)):
    """
    Returns an asynchronous session for the database engine.

    This function asynchronously creates and returns a session for the database engine. It is
    used to manage database transactions.

    Args:
        engine (AsyncEngine): The database engine to use for the session. Defaults to the engine
            returned by `get_engine`.

    Yields:
        AsyncSession: An asynchronous session for the database engine.
    """
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def get_user_controller(
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> UserController:
    """
    Returns the user controller.

    This function asynchronously returns the user controller instance. The user controller is
    responsible for managing user-related operations.

    Args:
        settings (Settings): The application settings. Defaults to the settings returned by `get_settings`.
        session (AsyncSession): The database session. Defaults to the session returned by `get_session`.

    Returns:
        UserController: The user controller instance.
    """
    return UserController(
        session,
        settings.jwt_secret_key,
        settings.jwt_encryption_algorithm,
        settings.resend_api_key,
        settings.environment,
    )


async def get_item_controller(
    session: AsyncSession = Depends(get_session),
) -> ItemController:
    """
    Returns the item controller.

    This function asynchronously returns the item controller instance. The item controller is
    responsible for managing item-related operations.

    Args:
        session (AsyncSession): The database session. Defaults to the session returned by `get_session`.

    Returns:
        ItemController: The item controller instance.
    """
    return ItemController(session)


async def get_stripe_service(settings: Settings = Depends(get_settings)):
    return StripeService(
        settings.stripe_secret_key,
        settings.frontend_success_url,
        settings.frontend_cancel_url,
    )


async def get_order_controller(
    session: AsyncSession = Depends(get_session),
    user_controller: UserController = Depends(get_user_controller),
) -> OrderController:
    """
    Returns the order controller.

    This function asynchronously returns the order controller instance. The order controller is
    responsible for managing order-related operations.

    Args:
        session (AsyncSession): The database session. Defaults to the session returned by `get_session`.
        user_controller (UserController): The user controller instance. Defaults to the instance returned by `get_user_controller`.

    Returns:
        OrderController: The order controller instance.
    """
    return OrderController(session, user_controller)


async def get_payment_controller(
    session: AsyncSession = Depends(get_session),
    stripe_service: StripeService = Depends(get_stripe_service),
    order_controller: OrderController = Depends(get_order_controller),
) -> PaymentController:
    """
    Returns the payment controller.

    This function asynchronously returns the payment controller instance. The payment controller is
    responsible for managing payment-related operations.

    Args:
        session (AsyncSession): The database session. Defaults to the session returned by `get_session`.
        stripe_service (StripeService): The Stripe service instance. Defaults to the instance returned by `get_stripe_service`.
        order_controller (OrderController): The order controller instance. Defaults to the instance returned by `get_order_controller`.

    Returns:
        PaymentController: The payment controller instance.
    """
    return PaymentController(session, stripe_service, order_controller)


async def get_wishlist_controller(
    session: AsyncSession = Depends(get_session),
) -> WishlistController:
    """
    Returns the wishlist controller.

    This function asynchronously returns the wishlist controller instance. The wishlist controller is
    responsible for managing wishlist-related operations.

    Args:
        session (AsyncSession): The database session. Defaults to the session returned by `get_session`.

    Returns:
        WishlistController: The wishlist controller instance.
    """
    return WishlistController(session)


async def get_chat_controller(
    session: AsyncSession = Depends(get_session),
    user_controller: UserController = Depends(get_user_controller),
    item_controller: ItemController = Depends(get_item_controller),
    order_controller: OrderController = Depends(get_order_controller),
) -> ChatController:
    """
    Returns the chat controller.

    This function asynchronously returns the chat controller instance. The chat controller is
    responsible for managing chat-related operations.

    Args:
        session (AsyncSession): The database session. Defaults to the session returned by `get_session`.
        user_controller (UserController): The user controller instance. Defaults to the instance returned by `get_user_controller`.
        item_controller (ItemController): The item controller instance. Defaults to the instance returned by `get_item_controller`.
        order_controller (OrderController): The order controller instance. Defaults to the instance returned by `get_order_controller`.

    Returns:
        ChatController: The chat controller instance.
    """
    return ChatController(session, user_controller, item_controller, order_controller)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_controller: UserController = Depends(get_user_controller),
) -> User:
    """
    Returns the current user based on the token.

    This function asynchronously returns the current user based on the provided token. It uses the
    user controller to validate the token and retrieve the user.

    Args:
        token (str): The token to use for authentication. Defaults to the token returned by `oauth2_scheme`.
        user_controller (UserController): The user controller instance. Defaults to the instance returned by `get_user_controller`.

    Returns:
        User: The current user instance.
    """
    user_email = await user_controller.get_current_user_token(token)
    return await user_controller.get_user(UserQuery(email=user_email))


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current active user.

    This function asynchronously returns the current active user. It checks if the user account is
    active and raises an exception if it is not.

    Args:
        current_user (User): The current user instance. Defaults to the instance returned by `get_current_user`.

    Returns:
        User: The current active user instance.
    """
    if current_user.is_active is False:
        raise UserAccountIsNotActive(username=current_user.username)
    return current_user


async def get_current_active_admin_user(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the current active admin user.

    This function asynchronously returns the current active admin user. It checks if the user is an
    admin and raises an exception if they are not.

    Args:
        current_user (User): The current active user instance. Defaults to the instance returned by `get_current_active_user`.

    Returns:
        User: The current active admin user instance.
    """
    if current_user.is_admin is False:
        raise UserNotAllowed(uuid=current_user.id, action="perform admin actions")
    return current_user
