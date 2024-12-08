from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import model_validator

from rizana.api.models.shared import DBModel
from rizana.api.models.table import (
    Address,
    BillingAddress,
    CharityContribution,
    Conversation,
    Favorite,
    Feedback,
    Item,
    Message,
    Order,
    OrderCancellation,
    PaymentMethod,
    Review,
    UserActivityLog,
    Wish,
)
from rizana.api.models.user import UserBase


class UserCreate(UserBase):
    """
    User creation schema.

    Attributes:
        password (str): The password for the user.
    """

    password: str


class UserQuery(DBModel):
    """
    Represents a query for a user based on various identifiers.

    Attributes:
        user_id (UUID | None): The unique identifier for the user.
        username (str | None): The username of the user.
        email (str | None): The email address of the user.
        emirate_id (str | None): The emirate ID of the user.

    Methods:
        check_that_at_least_one_param_is_set: Validates that at least one of the user_id, username, email, or emirate_id is provided.
    """

    user_id: UUID | None = None
    username: str | None = None
    email: str | None = None
    emirate_id: str | None = None

    @model_validator(mode="after")
    def check_that_at_least_one_param_is_set(self) -> Self:
        """
        Validates that at least one of the user_id, username, email, or emirate_id is provided.

        Raises:
            ValueError: If none of the user_id, username, email, or emirate_id is provided.
        """
        if not (self.user_id or self.username or self.email or self.emirate_id):
            raise ValueError(
                "At least one of user_id, username, email, or emirate_id must be provided"
            )
        return self


class ActivateUser(DBModel):
    """
    Represents the schema for activating a user.

    Attributes:
        user_id (UUID): The unique identifier of the user.
        activation_key (str): The activation key for the user.
    """

    user_id: UUID
    activation_key: str


class UserView(UserBase):
    """
    Represents a detailed view of a user with various relationships and attributes.
    Attributes:
        id (UUID): Unique identifier for the user.
        password (str): User's password.
        created_at (datetime): Timestamp when the user was created.
        is_active (bool): Indicates if the user is active. Defaults to True.
        is_admin (bool): Indicates if the user has admin privileges. Defaults to True.
        items (list[Item]): List of items associated with the user.
        orders (list[Order]): List of orders placed by the user.
        sales (list[Order]): List of sales made by the user.
        reviews (list[Review]): List of reviews written by the user.
        addresses (list[Address]): List of addresses associated with the user.
        payment_methods (list[PaymentMethod]): List of payment methods associated with the user.
        wishlist (list[Wish]): List of items in the user's wishlist.
        messages_sent (list[Message]): List of messages sent by the user.
        messages_received (list[Message]): List of messages received by the user.
        conversations_as_buyer (list[Conversation]): List of conversations where the user is the buyer.
        conversations_as_seller (list[Conversation]): List of conversations where the user is the seller.
        favorites (list[Favorite]): List of user's favorite items.
        feedback (list[Feedback]): List of feedback given by the user.
        activity_logs (list[UserActivityLog]): List of activity logs for the user.
        charity_contributions (list[CharityContribution]): List of charity contributions made by the user.
        billing_addresses (list[BillingAddress]): List of billing addresses associated with the user.
        cancellations (list[OrderCancellation]): List of order cancellations made by the user.
    """

    id: UUID
    password: str
    created_at: datetime
    is_active: bool = True
    is_admin: bool = True

    # Relationships
    items: list["Item"]
    orders: list["Order"]
    sales: list["Order"]
    reviews: list["Review"]
    addresses: list["Address"]
    payment_methods: list["PaymentMethod"]
    wishlist: list["Wish"]
    messages_sent: list["Message"]
    messages_received: list["Message"]
    conversations_as_buyer: list["Conversation"]
    conversations_as_seller: list["Conversation"]
    favorites: list["Favorite"]
    feedback: list["Feedback"]
    activity_logs: list["UserActivityLog"]
    charity_contributions: list["CharityContribution"]
    billing_addresses: list["BillingAddress"]
    cancellations: list["OrderCancellation"]
