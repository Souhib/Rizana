from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship

from rizana.api.models.chat import ChatBase
from rizana.api.models.item import (
    BaseItem,
    CategoryBase,
    FavoriteBase,
    FeedbackBase,
    ItemConditionBase,
)
from rizana.api.models.order import DiscountBase, OrderBase
from rizana.api.models.payment import PaymentMethodBase
from rizana.api.models.report import ReportBase
from rizana.api.models.review import ReviewBase
from rizana.api.models.shipping import ShippingBase
from rizana.api.models.transaction import TransactionHistoryBase
from rizana.api.models.user import (
    AddressBase,
    NotificationBase,
    UserActivityLogBase,
    UserBase,
)
from rizana.api.models.wishlist import WishlistBase


class Category(CategoryBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Relationships
    items: list["Item"] = Relationship(back_populates="category")


class Item(BaseItem, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_sold: bool = Field(default=False)
    user_id: int = Field(foreign_key="user.id")

    # Relationships
    user: "User" = Relationship(back_populates="items")
    category: "Category" = Relationship(back_populates="items")
    orders: list["Order"] = Relationship(back_populates="item")
    reviews: list["Review"] = Relationship(back_populates="item")
    wishlist: list["Wishlist"] = Relationship(back_populates="item")
    favorites: list["Favorite"] = Relationship(back_populates="item")


class User(UserBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    password: str = Field(min_length=5)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = False
    is_admin: bool = False

    # Relationships
    items: list["Item"] = Relationship(back_populates="user")
    orders: list["Order"] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={"foreign_keys": "Order.buyer_id"},
    )
    sales: list["Order"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={"foreign_keys": "Order.seller_id"},
    )
    reviews: list["Review"] = Relationship(back_populates="user")
    addresses: list["Address"] = Relationship(back_populates="user")
    payment_methods: list["PaymentMethod"] = Relationship(back_populates="user")
    wishlist: list["Wishlist"] = Relationship(back_populates="user")
    chats_sent: list["Chat"] = Relationship(
        back_populates="sender",
        sa_relationship_kwargs={"foreign_keys": "Chat.sender_id"},
    )
    chats_received: list["Chat"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={"foreign_keys": "Chat.receiver_id"},
    )
    favorites: list["Favorite"] = Relationship(back_populates="user")
    feedback: list["Feedback"] = Relationship(back_populates="user")
    activity_logs: list["UserActivityLog"] = Relationship(back_populates="user")


class Order(OrderBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    buyer_id: int = Field(foreign_key="user.id")
    seller_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    item: "Item" = Relationship(back_populates="orders")
    buyer: "User" = Relationship(
        back_populates="orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.buyer_id]"},
    )
    seller: "User" = Relationship(
        back_populates="sales",
        sa_relationship_kwargs={"foreign_keys": "[Order.seller_id]"},
    )


class Address(AddressBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="addresses")


class Review(ReviewBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="reviews")
    item: "Item" = Relationship(back_populates="reviews")


class Wishlist(WishlistBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="wishlist")
    item: "Item" = Relationship(back_populates="wishlist")


class PaymentMethod(PaymentMethodBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="payment_methods")


class Chat(ChatBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")

    # Relationships
    sender: "User" = Relationship(
        back_populates="chats_sent",
        sa_relationship_kwargs={"foreign_keys": "[Chat.sender_id]"},
    )
    receiver: "User" = Relationship(
        back_populates="chats_received",
        sa_relationship_kwargs={"foreign_keys": "[Chat.receiver_id]"},
    )


class Favorite(FavoriteBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")

    # Relationships
    user: "User" = Relationship(back_populates="favorites")
    item: "Item" = Relationship(back_populates="favorites")


class TransactionHistory(TransactionHistoryBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    order_id: int = Field(foreign_key="order.id")
    user_id: int = Field(foreign_key="user.id")

    # Relationships
    order: "Order" = Relationship()
    user: "User" = Relationship()


class ItemCondition(ItemConditionBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)


class Discount(DiscountBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)


class Shipping(ShippingBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    item_id: int = Field(foreign_key="item.id")
    user_id: int = Field(foreign_key="user.id")

    # Relationships
    item: "Item" = Relationship()
    user: "User" = Relationship()


class Report(ReportBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    reporter_id: int = Field(foreign_key="user.id")
    reported_user_id: int | None = Field(default=None, foreign_key="user.id")
    reported_item_id: int | None = Field(default=None, foreign_key="item.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    reporter: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Report.reporter_id]"}
    )
    reported_user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Report.reported_user_id]"}
    )
    reported_item: "Item" = Relationship()


class Notification(NotificationBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship()


class UserActivityLog(UserActivityLogBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")

    # Relationships
    user: "User" = Relationship(back_populates="activity_logs")


class Feedback(FeedbackBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="feedback")
