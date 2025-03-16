from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship

from rizana.api.models.chat import ConversationBase, MessageBase, ProposalBase
from rizana.api.models.item import (
    BaseItem,
    CategoryBase,
    FavoriteBase,
    FeedbackBase,
    ItemConditionBase,
)
from rizana.api.models.order import CharityContributionBase, DiscountBase, OrderBase
from rizana.api.models.payment import BillingAddressBase, PaymentBase, PaymentMethodBase
from rizana.api.models.report import ReportBase
from rizana.api.models.review import ReviewBase
from rizana.api.models.shared import DBModel, generate_activation_key
from rizana.api.models.shipping import ShippingBase

# from rizana.api.models.transaction import TransactionHistoryBase
from rizana.api.models.user import (
    AddressBase,
    NotificationBase,
    UserActivityLogBase,
    UserBase,
)
from rizana.api.models.wishlist import WishBase
from rizana.api.schemas.chat import ProposalStatus


class ItemCategoryLink(DBModel, table=True):
    """Junction table to link items and categories"""

    __mapper_args__ = {
        "confirm_deleted_rows": False,
    }

    item_id: UUID = Field(foreign_key="item.id", primary_key=True)
    category_id: UUID = Field(foreign_key="category.id", primary_key=True)


class ItemImage(DBModel, table=True):
    """Table to store images for each item"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    url: str = Field(max_length=255)
    item_id: UUID = Field(foreign_key="item.id")

    item: "Item" = Relationship(
        back_populates="images", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Category(CategoryBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Relationships
    items: list["Item"] = Relationship(
        back_populates="categories",
        link_model=ItemCategoryLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Item(BaseItem, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_sold: bool = Field(default=False)
    user_id: UUID = Field(foreign_key="user.id")

    # Relationships
    user: "User" = Relationship(
        back_populates="items", sa_relationship_kwargs={"lazy": "selectin"}
    )
    categories: list["Category"] = Relationship(
        back_populates="items",
        link_model=ItemCategoryLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    images: list["ItemImage"] = Relationship(
        back_populates="item", sa_relationship_kwargs={"lazy": "selectin"}
    )
    orders: list["Order"] = Relationship(
        back_populates="item", sa_relationship_kwargs={"lazy": "selectin"}
    )
    reviews: list["Review"] = Relationship(
        back_populates="item", sa_relationship_kwargs={"lazy": "selectin"}
    )
    wishlist: list["Wish"] = Relationship(
        back_populates="item", sa_relationship_kwargs={"lazy": "selectin"}
    )
    favorites: list["Favorite"] = Relationship(
        back_populates="item", sa_relationship_kwargs={"lazy": "selectin"}
    )
    conversations: list["Conversation"] = Relationship(
        back_populates="item", sa_relationship_kwargs={"lazy": "selectin"}
    )


class EmailActivation(DBModel, table=True):
    """Table to store email activation tokens"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    activation_key: str = Field(default_factory=generate_activation_key)
    created_at: datetime = Field(default_factory=datetime.now)
    is_activated: bool = Field(default=False)


class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    password: str = Field(min_length=5)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = False
    is_admin: bool = True

    # Relationships
    items: list["Item"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    orders: list["Order"] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.buyer_id]",
            "lazy": "selectin",
        },
    )
    sales: list["Order"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.seller_id]",
            "lazy": "selectin",
        },
    )
    reviews: list["Review"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    addresses: list["Address"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    payment_methods: list["PaymentMethod"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    wishlist: list["Wish"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    messages_sent: list["Message"] = Relationship(
        back_populates="sender",
        sa_relationship_kwargs={
            "foreign_keys": "[Message.sender_id]",
            "lazy": "selectin",
        },
    )
    messages_received: list["Message"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={
            "foreign_keys": "[Message.receiver_id]",
            "lazy": "selectin",
        },
    )
    conversations_as_buyer: list["Conversation"] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={
            "foreign_keys": "[Conversation.buyer_id]",
            "lazy": "selectin",
        },
    )
    conversations_as_seller: list["Conversation"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={
            "foreign_keys": "[Conversation.seller_id]",
            "lazy": "selectin",
        },
    )
    favorites: list["Favorite"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    feedback: list["Feedback"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    activity_logs: list["UserActivityLog"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    charity_contributions: list["CharityContribution"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    billing_addresses: list["BillingAddress"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    payments: list["Payment"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    cancellations: list["OrderCancellation"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Order(OrderBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    buyer_id: UUID = Field(foreign_key="user.id")
    seller_id: UUID = Field(foreign_key="user.id")
    total_price: float
    currency: str = Field(default="aed")
    created_at: datetime = Field(default_factory=datetime.now)
    payment_method_id: UUID = Field(foreign_key="payment_method.id")
    billing_address_id: UUID = Field(foreign_key="billing_address.id")
    payment_status: str = Field(default="pending")  # pending, paid, failed
    stripe_payment_intent_id: str | None = Field(default=None, nullable=True)

    # Relationships
    item: "Item" = Relationship(
        back_populates="orders", sa_relationship_kwargs={"lazy": "selectin"}
    )
    buyer: "User" = Relationship(
        back_populates="orders",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.buyer_id]",
            "lazy": "selectin",
        },
    )
    seller: "User" = Relationship(
        back_populates="sales",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.seller_id]",
            "lazy": "selectin",
        },
    )
    charity_contribution: "CharityContribution" = Relationship(
        back_populates="order", sa_relationship_kwargs={"lazy": "selectin"}
    )
    payment_method: "PaymentMethod" = Relationship(
        back_populates="orders",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.payment_method_id]",
            "lazy": "selectin",
        },
    )
    billing_address: "BillingAddress" = Relationship(
        back_populates="orders",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.billing_address_id]",
            "lazy": "selectin",
        },
    )
    cancellation: "OrderCancellation" = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    payment: "Payment" = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )


class OrderCancellation(DBModel, table=True):
    """Table to store cancellation details for orders"""

    user_id: UUID = Field(foreign_key="user.id")
    order_id: UUID = Field(primary_key=True, unique=True, foreign_key="order.id")
    cancellation_reason: str = Field(max_length=1000)
    canceled_at: datetime = Field(default_factory=datetime.now)

    order: "Order" = Relationship(
        back_populates="cancellation",
        sa_relationship_kwargs={
            "foreign_keys": "[OrderCancellation.order_id]",
            "lazy": "selectin",
        },
    )
    user: "User" = Relationship(
        back_populates="cancellations",
        sa_relationship_kwargs={
            "foreign_keys": "[OrderCancellation.user_id]",
            "lazy": "selectin",
        },
    )


class Address(AddressBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="addresses", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Review(ReviewBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")
    item_id: UUID = Field(foreign_key="item.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="reviews", sa_relationship_kwargs={"lazy": "selectin"}
    )
    item: "Item" = Relationship(
        back_populates="reviews", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Wish(WishBase, table=True):
    # id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="wishlist", sa_relationship_kwargs={"lazy": "selectin"}
    )
    item: "Item" = Relationship(
        back_populates="wishlist", sa_relationship_kwargs={"lazy": "selectin"}
    )


class BillingAddress(BillingAddressBase, table=True):
    __tablename__ = "billing_address"

    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="billing_addresses", sa_relationship_kwargs={"lazy": "selectin"}
    )
    orders: list["Order"] = Relationship(
        back_populates="billing_address",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.billing_address_id]",
            "lazy": "selectin",
        },
    )
    payments: list["Payment"] = Relationship(
        back_populates="billing_address",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )


class PaymentMethod(PaymentMethodBase, table=True):
    __tablename__ = "payment_method"

    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="payment_methods", sa_relationship_kwargs={"lazy": "selectin"}
    )
    orders: list["Order"] = Relationship(
        back_populates="payment_method",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.payment_method_id]",
            "lazy": "selectin",
        },
    )
    payments: list["Payment"] = Relationship(
        back_populates="payment_method",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )


class Message(MessageBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    sender_id: UUID = Field(foreign_key="user.id")
    conversation_id: UUID = Field(foreign_key="conversation.id")
    sent_at: datetime = Field(default_factory=datetime.now)
    is_read: bool = Field(default=False)

    # Relationships
    sender: "User" = Relationship(
        back_populates="messages_sent",
        sa_relationship_kwargs={
            "foreign_keys": "[Message.sender_id]",
            "lazy": "selectin",
        },
    )
    receiver: "User" = Relationship(
        back_populates="messages_received",
        sa_relationship_kwargs={
            "foreign_keys": "[Message.receiver_id]",
            "lazy": "selectin",
        },
    )
    conversation: "Conversation" = Relationship(
        back_populates="messages", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Conversation(ConversationBase, table=True):
    """Table to store conversations between two users for a specific item"""

    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    item: "Item" = Relationship(
        back_populates="conversations", sa_relationship_kwargs={"lazy": "selectin"}
    )
    buyer: "User" = Relationship(
        back_populates="conversations_as_buyer",
        sa_relationship_kwargs={
            "foreign_keys": "[Conversation.buyer_id]",
            "lazy": "selectin",
        },
    )
    seller: "User" = Relationship(
        back_populates="conversations_as_seller",
        sa_relationship_kwargs={
            "foreign_keys": "[Conversation.seller_id]",
            "lazy": "selectin",
        },
    )
    messages: list["Message"] = Relationship(
        back_populates="conversation", sa_relationship_kwargs={"lazy": "selectin"}
    )
    proposals: list["Proposal"] = Relationship(
        back_populates="conversation", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Proposal(ProposalBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    sender_id: UUID = Field(foreign_key="user.id")
    conversation_id: UUID = Field(foreign_key="conversation.id")
    created_at: datetime = Field(default_factory=datetime.now)
    status: ProposalStatus = Field(default=ProposalStatus.PENDING)

    # Relationships
    conversation: "Conversation" = Relationship(
        back_populates="proposals", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Favorite(FavoriteBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")
    item_id: UUID = Field(foreign_key="item.id")

    # Relationships
    user: "User" = Relationship(
        back_populates="favorites", sa_relationship_kwargs={"lazy": "selectin"}
    )
    item: "Item" = Relationship(
        back_populates="favorites", sa_relationship_kwargs={"lazy": "selectin"}
    )


# class TransactionHistory(TransactionHistoryBase, table=True):
#     id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
#     order_id: UUID = Field(foreign_key="order.id")
#     user_id: UUID = Field(foreign_key="user.id")
#     created_at: datetime = Field(default_factory=datetime.now)
#
#     # Relationships
#     order: "Order" = Relationship(
#         back_populates="transaction_history",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )
#     user: "User" = Relationship(
#         back_populates="transaction_history",
#         sa_relationship_kwargs={"lazy": "selectin"},
#     )


class ItemCondition(ItemConditionBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)


class Discount(DiscountBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)


class Shipping(ShippingBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    item_id: UUID = Field(foreign_key="item.id")
    user_id: UUID = Field(foreign_key="user.id")

    # Relationships
    item: "Item" = Relationship(sa_relationship_kwargs={"lazy": "selectin"})
    user: "User" = Relationship(sa_relationship_kwargs={"lazy": "selectin"})


class Report(ReportBase, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True, unique=True)
    reporter_id: UUID = Field(foreign_key="user.id")
    reported_user_id: UUID | None = Field(default=None, foreign_key="user.id")
    reported_item_id: UUID | None = Field(default=None, foreign_key="item.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    reporter: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Report.reporter_id]",
            "lazy": "selectin",
        }
    )
    reported_user: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Report.reported_user_id]",
            "lazy": "selectin",
        }
    )
    reported_item: "Item" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Report.reported_item_id]",
            "lazy": "selectin",
        }
    )


class Notification(NotificationBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(sa_relationship_kwargs={"lazy": "selectin"})


class UserActivityLog(UserActivityLogBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")

    # Relationships
    user: "User" = Relationship(
        back_populates="activity_logs", sa_relationship_kwargs={"lazy": "selectin"}
    )


class Feedback(FeedbackBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="feedback", sa_relationship_kwargs={"lazy": "selectin"}
    )


class CharityContribution(CharityContributionBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    order_id: UUID = Field(foreign_key="order.id")
    user_id: UUID = Field(foreign_key="user.id")

    # Relationships
    order: "Order" = Relationship(
        back_populates="charity_contribution",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    user: "User" = Relationship(
        back_populates="charity_contributions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Payment(PaymentBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUID = Field(foreign_key="user.id")
    billing_address_id: UUID = Field(foreign_key="billing_address.id")
    payment_method_id: UUID = Field(foreign_key="payment_method.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="payments", sa_relationship_kwargs={"lazy": "selectin"}
    )
    order: "Order" = Relationship(
        back_populates="payment",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    payment_method: "PaymentMethod" = Relationship(
        back_populates="payments",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    billing_address: "BillingAddress" = Relationship(
        back_populates="payments",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
