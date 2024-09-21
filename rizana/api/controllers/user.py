from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.table import User
from rizana.api.schemas.error import (
    EmailNotRecognizedError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WrongPasswordError,
)
from rizana.api.schemas.user import UserCreate, UserQuery


class UserController:
    def __init__(
        self, db: AsyncSession, jwt_secret_key: str, jwt_encryption_algorithm: str
    ):
        self.db = db
        self.JWT_SECRET_KEY = jwt_secret_key
        self.JWT_ENCRYPTION_ALGORITHM = jwt_encryption_algorithm
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.ph = PasswordHasher()

    async def get_user(self, user_query: UserQuery) -> User:
        try:
            if user_query.user_id:
                query = select(User).where(User.id == user_query.user_id)
            elif user_query.username:
                query = select(User).where(User.username == user_query.username)
            elif user_query.email:
                query = select(User).where(User.email == user_query.email)
            elif user_query.emirate_id:
                query = select(User).where(User.emirate_id == user_query.emirate_id)
            return (await self.db.exec(query)).one()
        except NoResultFound:
            raise UserNotFoundError(
                user_id=user_query.user_id,
                username=user_query.username,
                email=user_query.email,
                emirate_id=user_query.emirate_id,
            )

    async def create_user(self, user_create: UserCreate) -> User:
        try:
            new_user = User(**user_create.model_dump())
            new_user.password = await self._hash_user_password(new_user.password)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except IntegrityError:
            raise UserAlreadyExistsError(email_address=user_create.email)

    async def create_access_token(self, data: dict, expires_delta: timedelta = None):
        data["exp"] = datetime.now() + (
            expires_delta if expires_delta else timedelta(minutes=15)
        )
        encoded_jwt = jwt.encode(
            data, self.JWT_SECRET_KEY, algorithm=self.JWT_ENCRYPTION_ALGORITHM
        )
        return encoded_jwt

    async def get_current_user_token(self, token: str):
        try:
            payload = jwt.decode(
                token, self.JWT_SECRET_KEY, algorithms=[self.JWT_ENCRYPTION_ALGORITHM]
            )
            user_email: str = payload.get("sub")
            return user_email
        except JWTError:
            raise InvalidTokenError(token)

    async def _hash_user_password(self, password: str) -> str:
        return self.ph.hash(password)

    async def _verify_user_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        return self.ph.verify(hashed_password, plain_password)

    async def _authenticate_user(self, email_address: str, password: str) -> User:
        try:
            user = await self.get_user(UserQuery(email=email_address))
            await self._verify_user_password(password, user.password)
            return user
        except UserNotFoundError:
            raise EmailNotRecognizedError(email=email_address)
        except (InvalidHashError, VerifyMismatchError):
            raise WrongPasswordError

    async def login_user(self, form_data: OAuth2PasswordRequestForm):
        user = await self._authenticate_user(form_data.username, form_data.password)
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await self.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}
