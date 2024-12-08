import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import resend
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.table import EmailActivation, User
from rizana.api.schemas.error import (
    AccountAlreadyActivated,
    ActivationKeyExpired,
    ActivationKeyIncorrect,
    EmailNotRecognizedError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserIsInactive,
    UserNotFoundError,
    WrongPasswordError,
)
from rizana.api.schemas.user import UserCreate, UserQuery

from .email import email_body


class UserController:
    """
    Handles user-related operations such as user creation, authentication, and token generation.

    This class provides methods for creating new users, authenticating users, and generating access tokens.
    """

    def __init__(
        self,
        db: AsyncSession,
        jwt_secret_key: str,
        jwt_encryption_algorithm: str,
        resend_api_key: str,
    ):
        """
        Initializes the UserController with a database session, JWT secret key, and JWT encryption algorithm.

        Args:
            db (AsyncSession): The database session to use for operations.
            jwt_secret_key (str): The secret key used for JWT encryption.
            jwt_encryption_algorithm (str): The algorithm used for JWT encryption.
        """
        self.db = db
        self.JWT_SECRET_KEY = jwt_secret_key
        self.JWT_ENCRYPTION_ALGORITHM = jwt_encryption_algorithm
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.ph = PasswordHasher()
        self._set_resend_api_key(resend_api_key)

    def _set_resend_api_key(self, resend_api_key: str) -> None:
        resend.api_key = resend_api_key

    async def get_user(self, user_query: UserQuery) -> User:
        """
        Retrieves a user based on the provided query parameters.

        This method attempts to retrieve a user from the database based on the provided query parameters.
        If a user is found, it returns the user object. If not, it raises a UserNotFoundError.

        Args:
            user_query (UserQuery): The query parameters to use for user retrieval.

        Returns:
            User: The retrieved user object.

        Raises:
            UserNotFoundError: If no user is found matching the query parameters.
        """
        try:
            if user_query.user_id:
                query = select(User).where(User.id == user_query.user_id)
            elif user_query.username:
                query = select(User).where(User.username == user_query.username)
            elif user_query.email:
                query = select(User).where(User.email == user_query.email)
            elif user_query.emirate_id:
                query = select(User).where(User.emirate_id == user_query.emirate_id)
            user = (await self.db.exec(query)).one()
            if user.is_active:
                return user
            else:
                raise UserIsInactive(
                    user_id=user_query.user_id,
                    username=user_query.username,
                    email=user_query.email,
                    emirate_id=user_query.emirate_id,
                )
        except NoResultFound:
            raise UserNotFoundError(
                user_id=user_query.user_id,
                username=user_query.username,
                email=user_query.email,
                emirate_id=user_query.emirate_id,
            )

    async def get_inactive_user(self, user_id: UUID) -> User:
        """
        Retrieves an inactive user based on the provided user ID.

        This method attempts to retrieve an inactive user from the database based on the provided user ID.
        If an inactive user is found, it returns the user object. If not, it raises a UserIsInactive.

        Args:
            user_id (UUID): The unique identifier of the user to retrieve.

        Returns:
            User: The retrieved user object.

        Raises:
            UserIsInactive: If the user is found but is not active.
        """
        try:
            return (
                await self.db.exec(
                    select(User)
                    .where(User.id == user_id)
                    .where(User.is_active == False)
                )
            ).one()
        except NoResultFound:
            raise UserNotFoundError(user_id)

    async def create_user(self, user_create: UserCreate) -> User:
        """
        Creates a new user and adds them to the database.

        This method attempts to create a new user with the provided creation schema and adds them to the database.
        If the user creation is successful, it returns the newly created user object. If not, it raises a UserAlreadyExistsError.

        Args:
            user_create (UserCreate): The user creation schema.

        Returns:
            User: The newly created user object.

        Raises:
            UserAlreadyExistsError: If a user with the provided email already exists.
        """
        try:
            new_user = User(**user_create.model_dump())
            new_user.password = self._hash_user_password(new_user.password)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)

            email_activation = EmailActivation(user_id=new_user.id)
            self.db.add(email_activation)
            await self.db.commit()
            await self.db.refresh(email_activation)

            await self._send_activation_email(new_user, email_activation.activation_key)
            return new_user
        except IntegrityError as e:
            print(e)
            raise UserAlreadyExistsError(email_address=user_create.email)

    async def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ):
        """
        Generates an access token for the provided data with an optional expiration delta.

        This method generates an access token based on the provided data and an optional expiration delta.
        If an expiration delta is not provided, it defaults to 15 minutes.

        Args:
            data (dict): The data to encode in the token.
            expires_delta (timedelta, optional): The expiration delta for the token. Defaults to None.

        Returns:
            str: The generated access token.
        """
        expire = datetime.now(UTC) + (
            expires_delta if expires_delta else timedelta(minutes=15)
        )
        data["exp"] = int(expire.timestamp())
        encoded_jwt = jwt.encode(
            data, self.JWT_SECRET_KEY, algorithm=self.JWT_ENCRYPTION_ALGORITHM
        )
        return encoded_jwt

    async def get_current_user_token(self, token: str):
        """
        Extracts the user email from a provided token.

        This method attempts to decode the provided token and extract the user email.
        If the token is invalid, it raises an InvalidTokenError.

        Args:
            token (str): The token to decode.

        Returns:
            str: The email of the user associated with the token.

        Raises:
            InvalidTokenError: If the token is invalid.
        """
        try:
            payload = jwt.decode(
                token, self.JWT_SECRET_KEY, algorithms=[self.JWT_ENCRYPTION_ALGORITHM]
            )
            if payload.get("exp") < int(datetime.now(UTC).timestamp()):
                raise JWTError("Token has expired")
            user_email = payload.get("sub")
            return user_email
        except JWTError:
            raise InvalidTokenError(token)

    def _hash_user_password(self, password: str) -> str:
        """
        Hashes a user password using the Argon2 password hasher.

        Args:
            password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        return self.ph.hash(password)

    async def _verify_user_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """
        Verifies a user password against a hashed password using the Argon2 password hasher.

        Args:
            plain_password (str): The plain password to verify.
            hashed_password (str): The hashed password to verify against.

        Returns:
            bool: True if the password is valid, False otherwise.
        """
        return self.ph.verify(hashed_password, plain_password)

    async def _authenticate_user(self, email_address: str, password: str) -> User:
        """
        Authenticates a user based on their email and password.

        This method attempts to authenticate a user by first retrieving the user based on their email,
        then verifying their password against the hashed password in the database.
        If the authentication is successful, it returns the user object. If not, it raises an appropriate error.

        Args:
            email_address (str): The email address of the user to authenticate.
            password (str): The password of the user to authenticate.

        Returns:
            User: The authenticated user object.

        Raises:
            EmailNotRecognizedError: If the email address is not recognized.
            WrongPasswordError: If the password is incorrect.
        """
        try:
            user = await self.get_user(UserQuery(email=email_address))
            await self._verify_user_password(password, user.password)
            return user
        except UserNotFoundError:
            raise EmailNotRecognizedError(email=email_address)
        except (InvalidHashError, VerifyMismatchError):
            raise WrongPasswordError

    async def login_user(self, form_data: OAuth2PasswordRequestForm):
        """
        Handles user login and generates an access token.

        This method authenticates a user based on their email and password, then generates an access token for them.
        The access token is set to expire in 30 minutes.

        Args:
            form_data (OAuth2PasswordRequestForm): The form data containing the user's email and password.

        Returns:
            dict: A dictionary containing the access token and its type.
        """
        user = await self._authenticate_user(form_data.username, form_data.password)
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await self.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}

    async def _send_activation_email(
        self, user: User, activation_key: str
    ) -> resend.Email:
        """
        Sends an activation email to the specified user.
        Args:
            user (User): The user to whom the activation email will be sent.
            activation_key (str): The activation key to be included in the email.
        Returns:
            resend.Email: The email object that was sent.
        """
        body = (
            email_body.replace("[User's Name]", user.username)
            .replace("[Your Company Name]", "Rizana")
            .replace("[User ID]", str(user.id))
            .replace("[User Activation Key]", activation_key)
        )
        params: resend.Emails.SendParams = {
            "from": "onboarding@resend.dev",
            "to": [user.email],
            "subject": "Rizana Activation Email",
            "html": body,
        }

        email: resend.Email = await asyncio.to_thread(resend.Emails.send, params)
        return email

    async def _check_activation_key(self, user_id: UUID, activation_key: str) -> None:
        """
        Check if the provided activation key is valid for the given user.

        This method verifies if the activation key matches the one stored in the database
        for the specified user. It also checks if the activation key has already been used
        or if it has expired.

        Args:
            user_id (UUID): The unique identifier of the user.
            activation_key (str): The activation key to be verified.

        Raises:
            AccountAlreadyActivated: If the account has already been activated.
            ActivationKeyExpired: If the activation key has expired.
            ActivationKeyIncorrect: If the activation key is incorrect or not found.
        """
        try:
            email_activation = (
                await self.db.exec(
                    select(EmailActivation)
                    .where(EmailActivation.user_id == user_id)
                    .where(EmailActivation.activation_key == activation_key)
                )
            ).one()
            if email_activation.is_activated:
                raise AccountAlreadyActivated(user_id=user_id)
            if email_activation.created_at < datetime.now() - timedelta(minutes=30):
                raise ActivationKeyExpired(
                    user_id=user_id,
                    activation_key=activation_key,
                )
            email_activation.is_activated = True
            await self.db.commit()
        except NoResultFound:
            raise ActivationKeyIncorrect(
                user_id=user_id,
                activation_key=activation_key,
            )

    async def _get_latest_active_activation_key(self, user_id: UUID) -> str:
        """
        Retrieves the latest active activation key for the specified user.

        This method retrieves the latest active activation key for the specified user.

        Args:
            user_id (UUID): The unique identifier of the user.

        Returns:
            str: The latest active activation key for the user.
        """
        email_activation = (
            await self.db.exec(
                select(EmailActivation)
                .where(EmailActivation.user_id == user_id)
                .where(EmailActivation.is_activated == False)
            )
        ).one()
        if email_activation.created_at < datetime.now() - timedelta(minutes=30):
            raise ActivationKeyExpired(
                user_id=user_id,
                activation_key=email_activation.activation_key,
            )
        return email_activation.activation_key

    async def set_user_admin(self, user_id: UUID) -> User:
        """
        Set user as admin.
        Args:
            user_id (UUID): The unique identifier of the user.
        Returns:
            User: The user object.
        Raises:
            UserNotFoundError: If the user with the given ID does not exist.
        """
        user = await self.get_user(UserQuery(user_id=user_id))
        user.is_admin = True
        await self.db.commit()
        return user

    async def activate_user(self, user_id: UUID, token: str) -> User:
        """
        Activate a user account.
        Args:
            user_id (UUID): The unique identifier of the user.
            token (str): The activation token.
        Returns:
            User: The activated user object.
        Raises:
            UserNotFoundError: If the user with the given ID does not exist.
            InvalidTokenError: If the provided activation token is invalid.
        """

        user = await self.get_inactive_user(user_id)
        await self._check_activation_key(user_id, token)
        user.is_active = True
        await self.db.commit()
        return user
