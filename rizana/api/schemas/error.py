from uuid import UUID


class BaseError(Exception):
    def __init__(self, name: str, message: str, status_code: int):
        self.name = name
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFoundError(BaseError):
    def __init__(
        self,
        user_id: UUID | None = None,
        email: str | None = None,
        emirate_id: str | None = None,
        username: str | None = None,
        status_code: int = 404,
        name: str = "UserNotFoundError",
    ):
        self.name = name
        self.status_code = status_code

        identifier = user_id or email or emirate_id or username
        identifier_type = (
            "id"
            if user_id
            else "email" if email else "emirate ID" if emirate_id else "username"
        )

        self.message = f"User with {identifier_type} {identifier} not found"
        super().__init__(
            name=self.name, message=self.message, status_code=self.status_code
        )


class UserAlreadyExistsError(BaseError):
    def __init__(
        self,
        email_address: str,
        status_code: int = 409,
        name: str = "UserAlreadyExistsError",
    ):
        self.name = name
        self.message = f"User with email address {email_address} already exists"
        self.status_code = status_code
        super().__init__(
            name=self.name, message=self.message, status_code=self.status_code
        )


class InvalidTokenError(BaseError):
    def __init__(
        self, token: str, status_code: int = 401, name: str = "InvalidTokenError"
    ):
        self.name = name
        self.status_code = status_code
        self.message = f"Invalid token: {token}"
        super().__init__(
            name=self.name, message=self.message, status_code=self.status_code
        )


class EmailNotRecognizedError(BaseError):
    def __init__(self, email: str, status_code: int = 401):
        super().__init__(
            name="EmailNotRecognizedError",
            message=f"Email {email} not recognized",
            status_code=status_code,
        )


class WrongPasswordError(BaseError):
    def __init__(self, message: str = "Wrong password", status_code: int = 401):
        super().__init__(
            name="WrongPasswordError", message=message, status_code=status_code
        )


class UserAccountIsNotActive(BaseError):
    def __init__(
        self,
        username: str,
        name: str = "UserAccountIsNotActive",
        status_code: int = 403,
    ):
        super().__init__(
            name=name,
            message=f"User {username} account has is not active",
            status_code=status_code,
        )


class UserNotAllowed(BaseError):
    def __init__(
        self, username: str, name: str = "UserNotAllowed", status_code: int = 403
    ):
        super().__init__(
            name=name,
            message=f"User {username} account is not allowed to perform this action",
            status_code=status_code,
        )


class CategoryAlreadyExist(BaseError):
    def __init__(
        self,
        category_name: str,
        name: str = "CategoryAlreadyExist",
        status_code: int = 409,
    ):
        super().__init__(
            name=name,
            message=f"Category {category_name} already exists",
            status_code=status_code,
        )


class ItemsDependsOnCategory(BaseError):
    def __init__(
        self,
        category_name: str,
        name: str = "ItemsDependsOnCategory",
        status_code: int = 409,
    ):
        super().__init__(
            name=name,
            message=f"Some items still depend on {category_name} category, you should delete these items before deleting this category",
            status_code=status_code,
        )
