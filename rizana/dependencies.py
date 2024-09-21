from functools import lru_cache

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.item import ItemController
from rizana.api.controllers.user import UserController
from rizana.api.models.table import User
from rizana.api.schemas.error import UserAccountIsNotActive, UserNotAllowed
from rizana.api.schemas.user import UserQuery
from rizana.database import create_app_engine
from rizana.settings import Settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@lru_cache()
def get_settings():
    return Settings()


async def get_engine():
    return await create_app_engine()


async def get_session(engine: AsyncEngine = Depends(get_engine)):
    async with AsyncSession(engine) as session:
        yield session


async def get_user_controller(
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> UserController:
    return UserController(
        session, settings.jwt_secret_key, settings.jwt_encryption_algorithm
    )


async def get_item_controller(
    session: AsyncSession = Depends(get_session),
) -> ItemController:
    return ItemController(session)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_controller: UserController = Depends(get_user_controller),
) -> User:
    user_email = await user_controller.get_current_user_token(token)
    return await user_controller.get_user(UserQuery(email=user_email))


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if current_user.is_active is False:
        raise UserAccountIsNotActive(username=current_user.username)
    return current_user


async def get_current_active_admin_user(
    current_user: User = Depends(get_current_active_user),
):
    if current_user.is_admin is False:
        UserNotAllowed(username=current_user.username)
    return current_user
