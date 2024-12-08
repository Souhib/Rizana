from uuid import UUID

from loguru import logger


class BaseError(Exception):
    """
    Base class for custom exceptions.

    Args:
        name (str): The name of the error.
        message (str): The error message.
        status_code (int): The HTTP status code associated with the error.
    """

    def __init__(self, name: str, message: str, status_code: int):
        self.name = name
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFoundError(BaseError):
    """
    Exception raised when a user is not found based on the provided criteria.

    Args:
        user_id (UUID | None): The unique identifier of the user. Defaults to None.
        email (str | None): The email address of the user. Defaults to None.
        emirate_id (str | None): The emirate ID of the user. Defaults to None.
        username (str | None): The username of the user. Defaults to None.
        status_code (int): The HTTP status code for the error. Defaults to 404.
        name (str): The name of the error. Defaults to "UserNotFoundError".
    """

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
            else "email"
            if email
            else "emirate ID"
            if emirate_id
            else "username"
        )

        self.message = "We couldn't find a user that satisfies the provided criteria. Please check your input and try again."
        logger.warning(f"User with {identifier_type} {identifier} not found")
        super().__init__(
            name=self.name, message=self.message, status_code=self.status_code
        )


class UserAlreadyExistsError(BaseError):
    """
    Exception raised when a user with the given email address already exists.

    Args:
        email_address (str): The email address of the user that already exists.
        status_code (int, optional): The HTTP status code for the error. Defaults to 409.
        name (str, optional): The name of the error. Defaults to "UserAlreadyExistsError".
    """

    def __init__(
        self,
        email_address: str,
        status_code: int = 409,
        name: str = "UserAlreadyExistsError",
    ):
        self.name = name
        self.message = "User with this email address already exists"
        self.status_code = status_code
        logger.warning(f"User with email address {email_address} already exists")
        super().__init__(
            name=self.name, message=self.message, status_code=self.status_code
        )


class InvalidTokenError(BaseError):
    """
    Exception raised for invalid tokens.

    Args:
        token (str): The invalid token.
        status_code (int, optional): HTTP status code, defaults to 401.
        name (str, optional): Name of the error, defaults to "InvalidTokenError".
    """

    def __init__(
        self, token: str, status_code: int = 401, name: str = "InvalidTokenError"
    ):
        self.name = name
        self.status_code = status_code
        self.message = f"Invalid token: {token}"
        logger.warning(f"Invalid token: {token}")
        super().__init__(
            name=self.name, message=self.message, status_code=self.status_code
        )


class EmailNotRecognizedError(BaseError):
    """
    Exception raised when an unrecognized email is encountered.

    This error is typically used to indicate that the provided email address
    does not match any known records.

    Args:
        email (str): The email address that was not recognized.
        status_code (int, optional): The HTTP status code to return. Defaults to 401.
    """

    def __init__(self, email: str, status_code: int = 401):
        logger.warning(f"Email {email} not recognized")
        super().__init__(
            name="EmailNotRecognizedError",
            message="The email you entered is not recognized",
            status_code=status_code,
        )


class WrongPasswordError(BaseError):
    """
    Exception raised for errors in the input password.

    Args:
        message (str, optional): Custom error message. Defaults to "The password you entered is incorrect".
        status_code (int, optional): HTTP status code. Defaults to 401.
    """

    def __init__(
        self,
        message: str = "The password you entered is incorrect",
        status_code: int = 401,
    ):
        logger.warning("Incorrect password entered")
        super().__init__(
            name="WrongPasswordError", message=message, status_code=status_code
        )


class UserAccountIsNotActive(BaseError):
    """
    Exception raised when a user account is not active.

    Args:
        username (str): The username of the account.
        name (str, optional): The name of the error. Defaults to "UserAccountIsNotActive".
        status_code (int, optional): The HTTP status code for the error. Defaults to 403.
    """

    def __init__(
        self,
        username: str,
        name: str = "UserAccountIsNotActive",
        status_code: int = 403,
    ):
        logger.warning(f"User {username} account has is not active")
        super().__init__(
            name=name,
            message="Your account is not active",
            status_code=status_code,
        )


class UserNotAllowed(BaseError):
    """
    Exception raised when a user is not allowed to perform a specific action.

    Args:
        uuid (UUID): The unique identifier of the user.
        action (str): The action the user attempted to perform.
        name (str, optional): The name of the error. Defaults to "UserNotAllowed".
        status_code (int, optional): The HTTP status code for the error. Defaults to 403.
    """

    def __init__(
        self,
        uuid: UUID,
        action: str,
        name: str = "UserNotAllowed",
        status_code: int = 403,
    ):
        logger.warning(f"User {uuid} is not allowed to {action}")
        super().__init__(
            name=name,
            message="You're not allowed to perform this action",
            status_code=status_code,
        )


class CategoryDoesNotExist(BaseError):
    """
    Exception raised when a specified category does not exist.

    Args:
        category_name (str): The name of the category that does not exist.
        name (str, optional): The name of the error. Defaults to "CategoryDoesNotExist".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        category_name: str,
        name: str = "CategoryDoesNotExist",
        status_code: int = 404,
    ):
        logger.warning(f"Category {category_name} does not exist")
        super().__init__(
            name=name,
            message="The category you're looking for does not exist",
            status_code=status_code,
        )


class CategoryAlreadyExist(BaseError):
    """
    Exception raised when attempting to create a category that already exists.

    Args:
        category_name (str): The name of the category that already exists.
        name (str, optional): The name of the error. Defaults to "CategoryAlreadyExist".
        status_code (int, optional): The HTTP status code for the error. Defaults to 409.
    """

    def __init__(
        self,
        category_name: str,
        name: str = "CategoryAlreadyExist",
        status_code: int = 409,
    ):
        logger.warning(f"Category {category_name} already exists")
        super().__init__(
            name=name,
            message="The category you're trying to create already exists",
            status_code=status_code,
        )


class ItemsDependsOnCategory(BaseError):
    """
    Exception raised when attempting to delete a category that still has dependent items.

    This exception is used to indicate that there are items which still depend on the specified category,
    and these items must be deleted before the category can be deleted.

    Args:
        category_name (str): The name of the category that has dependent items.
        name (str, optional): The name of the exception. Defaults to "ItemsDependsOnCategory".
        status_code (int, optional): The HTTP status code for the exception. Defaults to 409.
    """

    def __init__(
        self,
        category_name: str,
        name: str = "ItemsDependsOnCategory",
        status_code: int = 409,
    ):
        logger.warning(
            f"Some items still depend on {category_name} category, you should delete these items before deleting this category"
        )
        super().__init__(
            name=name,
            message="Some items still depend on this category, you should delete these items before deleting this category",
            status_code=status_code,
        )


class ItemDoesNotExist(BaseError):
    """
    Exception raised when an item does not exist.

    Args:
        item_id (UUID): The unique identifier of the item.
        name (str, optional): The name of the error. Defaults to "ItemDoesNotExist".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        item_id: UUID,
        name: str = "ItemDoesNotExist",
        status_code: int = 404,
    ):
        logger.warning(f"Item with ID {item_id} does not exist")
        super().__init__(
            name=name,
            message="The item you're looking for does not exist",
            status_code=status_code,
        )


class ItemImageDoesNotExist(BaseError):
    """
    Exception raised when an item image does not exist.

    Args:
        image_id (UUID): The ID of the image that does not exist.
        name (str, optional): The name of the error. Defaults to "ItemImageDoesNotExist".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        image_id: UUID,
        name: str = "ItemImageDoesNotExist",
        status_code: int = 404,
    ):
        logger.warning(f"Item image with ID {image_id} does not exist")
        super().__init__(
            name=name,
            message="The item image you're looking for does not exist",
            status_code=status_code,
        )


class NoLinkBetweenCategoryAndItem(BaseError):
    """
    Exception raised when there is no link between a given item and category.

    Args:
        item_id (UUID): The unique identifier of the item.
        category_id (UUID): The unique identifier of the category.
        name (str, optional): The name of the error. Defaults to "NoLinkBetweenCategoryAndItem".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        item_id: UUID,
        category_id: UUID,
        name: str = "NoLinkBetweenCategoryAndItem",
        status_code: int = 404,
    ):
        logger.warning(
            f"No match found between item ID {item_id} and category ID {category_id}."
        )
        super().__init__(
            name=name,
            message="No match found between this item and category.",
            status_code=status_code,
        )


class PaymentMethodCreationError(BaseError):
    """
    Exception raised when a payment method creation fails.

    This error is raised when the system is unable to create a payment method for a user.

    Args:
        user_id (UUID): The unique identifier of the user for whom the payment method creation failed.
        status_code (int, optional): The HTTP status code to return. Defaults to 400.
    """

    def __init__(self, user_id: UUID, status_code: int = 400):
        logger.warning(f"Could not create a Payment Method for user {user_id}")
        super().__init__(
            name="PaymentMethodCreationError",
            message="We couldn't create a payment method for you. Please try again.",
            status_code=status_code,
        )


class PaymentMethodDoesNotExist(BaseError):
    """
    Exception raised when a payment method does not exist.

    This exception is used to indicate that a payment method with a given ID
    could not be found in the system.

    Args:
        payment_method_id (UUID): The ID of the payment method that does not exist.
        name (str, optional): The name of the error. Defaults to "PaymentMethodDoesNotExist".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        payment_method_id: UUID,
        name: str = "PaymentMethodDoesNotExist",
        status_code: int = 404,
    ):
        logger.warning(f"Payment method with ID {payment_method_id} does not exist")
        super().__init__(
            name=name,
            message="The payment method you're looking for does not exist",
            status_code=status_code,
        )


class ItemAlreadyInWishList(BaseError):
    """
    Exception raised when an item is already in the user's wishlist.

    Args:
        item_id (UUID): The unique identifier of the item.
        user_id (UUID): The unique identifier of the user.
        name (str): The name of the error. Defaults to "ItemAlreadyInWishList".
        status_code (int): The HTTP status code for the error. Defaults to 409.
    """

    def __init__(
        self,
        item_id: UUID,
        user_id: UUID,
        name: str = "ItemAlreadyInWishList",
        status_code: int = 409,
    ):
        logger.warning(f"Item {item_id} is already in wishlist of the user {user_id}")
        super().__init__(
            name=name,
            message="This item is already in your wishlist",
            status_code=status_code,
        )


class WishDoesNotExists(BaseError):
    """
    Exception raised when a wish does not exist.

    This exception is used to indicate that a wish with the specified item ID and user ID does not exist in the system.

    Args:
        item_id (UUID): The unique identifier of the item.
        user_id (UUID): The unique identifier of the user.
        name (str, optional): The name of the exception. Defaults to "WishDoesNotExists".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        item_id: UUID,
        user_id: UUID,
        name: str = "WishDoesNotExists",
        status_code: int = 404,
    ):
        logger.warning(
            f"Wish with item ID {item_id} and user ID {user_id} does not exist"
        )
        super().__init__(
            name=name,
            message="The wish you're looking for does not exist",
            status_code=status_code,
        )


class ProposalNotFoundError(BaseError):
    """
    Exception raised when a proposal is not found.

    Args:
        proposal_id (UUID): The ID of the proposal that was not found.
        name (str): The name of the error. Defaults to "ProposalNotFoundError".
        status_code (int): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        proposal_id: UUID,
        name: str = "ProposalNotFoundError",
        status_code: int = 404,
    ):
        logger.warning(f"Proposal with ID {proposal_id} does not exist")
        super().__init__(
            name=name,
            message="The proposal you're looking for does not exist",
            status_code=status_code,
        )


class ConversationNotFoundError(BaseError):
    """
    Exception raised when a conversation is not found.

    Args:
        conversation_id (UUID): The ID of the conversation that was not found.
        name (str, optional): The name of the error. Defaults to "ConversationNotFoundError".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        conversation_id: UUID,
        name: str = "ConversationNotFoundError",
        status_code: int = 404,
    ):
        logger.warning(f"Conversation with ID {conversation_id} does not exist")
        super().__init__(
            name=name,
            message="The conversation you're looking for does not exist",
            status_code=status_code,
        )


class ConversationNotFoundErrorByUsers(BaseError):
    """
    Exception raised when a conversation between a buyer and seller for a specific item is not found.

    Args:
        buyer_id (UUID): The unique identifier of the buyer.
        seller_id (UUID): The unique identifier of the seller.
        item_id (UUID): The unique identifier of the item.
        name (str, optional): The name of the error. Defaults to "ConversationNotFoundError".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self,
        buyer_id: UUID,
        seller_id: UUID,
        item_id: UUID,
        name: str = "ConversationNotFoundError",
        status_code: int = 404,
    ):
        logger.warning(
            f"Conversation with buyer ID {buyer_id} and seller ID {seller_id} for item {item_id} does not exist"
        )
        super().__init__(
            name=name,
            message="The conversation you're looking for does not exist",
            status_code=status_code,
        )


class UserCantAddHisOwnItemToWishlist(BaseError):
    """
    Exception raised when a user tries to add their own item to their wishlist.

    Args:
        item_id (UUID): The unique identifier of the item.
        username (str): The username of the user attempting the action.
        name (str, optional): The name of the error. Defaults to "UserCantAddHisOwnItemToWishlist".
        status_code (int, optional): The HTTP status code for the error. Defaults to 409.
    """

    def __init__(
        self,
        item_id: UUID,
        username: str,
        name: str = "UserCantAddHisOwnItemToWishlist",
        status_code: int = 409,
    ):
        logger.warning(
            f"User {username} is trying to add his own item {item_id} to wishlist"
        )
        super().__init__(
            name=name,
            message="You can't add your own item to your wishlist",
            status_code=status_code,
        )


class UserIsInactive(BaseError):
    """
    Exception raised when a user is inactive.

    This exception is used to indicate that a user's account is not active and
    therefore they are not allowed to perform certain actions.

    Args:
        user_id (UUID | None): The unique identifier of the user. Defaults to None.
        username (str | None): The username of the user. Defaults to None.
        email (str | None): The email address of the user. Defaults to None.
        emirate_id (str | None): The emirate ID of the user. Defaults to None.
        name (str): The name of the error. Defaults to "UserIsInactive".
        status_code (int): The HTTP status code for the error. Defaults to 403.
    """

    def __init__(
        self,
        user_id: UUID | None = None,
        username: str | None = None,
        email: str | None = None,
        emirate_id: str | None = None,
        name: str = "UserIsInactive",
        status_code: int = 403,
    ):
        identifier = user_id or username or email or emirate_id
        identifier_type = (
            "id"
            if user_id
            else "username"
            if username
            else "email"
            if email
            else "emirate ID"
        )
        logger.warning(f"User with {identifier_type} {identifier} is inactive")
        super().__init__(
            name=name, message="Your account is not active", status_code=status_code
        )


class OrderNotFoundError(BaseError):
    """
    Exception raised when an order is not found.

    This exception is used to indicate that an order with the specified ID does not exist in the system.

    Args:
        order_id (UUID): The ID of the order that was not found.
        name (str, optional): The name of the error. Defaults to "OrderNotFoundError".
        status_code (int, optional): The HTTP status code for the error. Defaults to 404.
    """

    def __init__(
        self, order_id: UUID, name: str = "OrderNotFoundError", status_code: int = 404
    ):
        logger.warning(f"Order with ID {order_id} does not exist")
        super().__init__(
            name=name,
            message="The order you're looking for does not exist",
            status_code=status_code,
        )


class ActivationKeyIncorrect(BaseError):
    """
    Exception raised when an incorrect activation key is provided.

    Args:
        user_id (UUID): The ID of the user attempting to activate.
        activation_key (str): The incorrect activation key provided.
        name (str, optional): The name of the error. Defaults to "ActivationKeyIncorrect".
        status_code (int, optional): The HTTP status code for the error. Defaults to 400.
    """

    def __init__(
        self,
        user_id: UUID,
        activation_key: str,
        name: str = "ActivationKeyIncorrect",
        status_code: int = 400,
    ):
        logger.warning(
            f"Activation key {activation_key} is incorrect for user {user_id}"
        )
        super().__init__(
            name=name,
            message="The activation key you entered is incorrect",
            status_code=status_code,
        )


class ActivationKeyExpired(BaseError):
    """
    Exception raised when an activation key is expired.

    Args:
        user_id (UUID): The ID of the user.
        activation_key (str): The expired activation key.
        name (str): The name of the error. Defaults to "ActivationKeyExpired".
        status_code (int): The HTTP status code for the error. Defaults to 400.
    """

    def __init__(
        self,
        user_id: UUID,
        activation_key: str,
        name: str = "ActivationKeyExpired",
        status_code: int = 400,
    ):
        logger.warning(f"Activation key {activation_key} is expired for user {user_id}")
        super().__init__(
            name=name,
            message="The activation key you entered is expired",
            status_code=status_code,
        )


class AccountAlreadyActivated(BaseError):
    """
    Exception raised when an attempt is made to activate an already activated account.

    Args:
        user_id (UUID): The unique identifier of the user.
        name (str, optional): The name of the error. Defaults to "AccountAlreadyActivated".
        status_code (int, optional): The HTTP status code for the error. Defaults to 400.
    """

    def __init__(
        self,
        user_id: UUID,
        name: str = "AccountAlreadyActivated",
        status_code: int = 400,
    ):
        logger.warning(f"Account for user {user_id} is already activated")
        super().__init__(
            name=name,
            message="Your account is already activated",
            status_code=status_code,
        )
