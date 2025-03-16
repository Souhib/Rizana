import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.chat import ChatController
from rizana.api.controllers.item import ItemController
from rizana.api.controllers.order import OrderController
from rizana.api.controllers.payment import PaymentController
from rizana.api.controllers.user import UserController
from rizana.api.controllers.wishlist import WishlistController
from rizana.api.models.order import CharityContributionBase, OrderStatus
from rizana.api.models.payment import CardType
from rizana.api.schemas.chat import MessageCreate, ProposalCreate
from rizana.api.schemas.item import CategoryCreate, ItemCreate
from rizana.api.schemas.order import OrderCreate
from rizana.api.schemas.payment import PaymentMethodCreate
from rizana.api.schemas.user import UserCreate
from rizana.api.schemas.wishlist import WishCreate
from rizana.database import create_app_engine, create_db_and_tables
from rizana.settings import Settings


async def create_data(db: AsyncSession):
    settings = Settings()
    user_controller = UserController(
        db, settings.jwt_secret_key, settings.jwt_encryption_algorithm
    )
    item_controller = ItemController(db)
    order_controller = OrderController(db, user_controller)
    payment_controller = PaymentController(db)
    chat_controller = ChatController(
        db, user_controller, item_controller, order_controller
    )
    wishlist_controller = WishlistController(db)

    # Create admin user
    admin_user = UserCreate(
        username="admin_user",
        email="admin@example.com",
        password="string",
        emirate_id="784-1234-1234567-1",
        country="ARE",
    )
    admin = await user_controller.create_user(admin_user)

    # Create normal user
    normal_user = UserCreate(
        username="normal_user",
        email="user@example.com",
        password="string",
        emirate_id="784-1234-1234567-2",
        country="ARE",
    )
    user = await user_controller.create_user(normal_user)

    # Create categories
    category1 = await item_controller.create_category(
        CategoryCreate(name="Electronics")
    )
    category2 = await item_controller.create_category(CategoryCreate(name="Books"))

    # Create payment method for normal user
    payment_method_user = PaymentMethodCreate(
        card_type=CardType.VISA,
        card_number="4111111111111111",
        expiry_date="12/25",
        billing_street="123 Main St",
        billing_city="Dubai",
        billing_state="Dubai",
        billing_country="ARE",
        billing_postal_code="00000",
    )

    await payment_controller.create_payment(payment_method_user, user.id)

    # Create payment method for admin user
    payment_method_admin = PaymentMethodCreate(
        card_type=CardType.MASTERCARD,
        card_number="5555555555554444",
        expiry_date="01/30",
        billing_street="456 Admin St",
        billing_city="Dubai",
        billing_state="Dubai",
        billing_country="ARE",
        billing_postal_code="11111",
    )

    await payment_controller.create_payment(payment_method_admin, admin.id)

    # Create items
    item1_admin = await item_controller.create_item(
        ItemCreate(
            title="Admin Item 1",
            description="Description for admin item 1",
            price=100.0,
            images=["http://example.com/image1.jpg"],
            categories=[category1.name],
        ),
        admin.id,
    )

    item2_admin = await item_controller.create_item(
        ItemCreate(
            title="Admin Item 2",
            description="Description for admin item 2",
            price=150.0,
            images=["http://example.com/image2.jpg"],
            categories=[category2.name],
        ),
        admin.id,
    )

    item1_user = await item_controller.create_item(
        ItemCreate(
            title="User Item 1",
            description="Description for user item 1",
            price=50.0,
            images=["http://example.com/image3.jpg"],
            categories=[category1.name],
        ),
        user.id,
    )

    item2_user = await item_controller.create_item(
        ItemCreate(
            title="User Item 2",
            description="Description for user item 2",
            price=75.0,
            images=["http://example.com/image4.jpg"],
            categories=[category2.name],
        ),
        user.id,
    )

    # Create orders
    order_admin = OrderCreate(
        item_id=item1_admin.id,
        total_price=item1_admin.price,
        status=OrderStatus.PENDING,
        buyer_id=user.id,
        seller_id=admin.id,
        charity_contribution=CharityContributionBase(amount=5.0, is_rounded=False),
    )
    order_user = OrderCreate(
        item_id=item1_user.id,
        total_price=item1_user.price,
        status=OrderStatus.PENDING,
        buyer_id=admin.id,
        seller_id=user.id,
        charity_contribution=CharityContributionBase(amount=2.5, is_rounded=True),
    )
    await order_controller.create_order(order_admin)
    await order_controller.create_order(order_user)

    # Create conversation
    conversation = await chat_controller.create_conversation(
        user.id, admin.id, item1_admin.id
    )

    # Create chat messages
    message1 = MessageCreate(
        sender_id=admin.id,
        receiver_id=user.id,
        message="Hello, I'm interested in your item.",
        conversation_id=conversation.id,
    )
    await chat_controller.send_message(admin.id, message1)

    message2 = MessageCreate(
        sender_id=user.id,
        receiver_id=admin.id,
        message="Great! Do you have any questions?",
        conversation_id=conversation.id,
    )
    await chat_controller.send_message(user.id, message2)

    # Create proposals
    proposal1 = ProposalCreate(
        item_id=item1_admin.id, proposed_price=90.0, conversation_id=conversation.id
    )
    await chat_controller.create_proposal(user.id, proposal1)

    # Create wishlist items
    wish1 = WishCreate(user_id=user.id, item_id=item2_admin.id)
    await wishlist_controller.create_wish(wish1, user)

    wish2 = WishCreate(user_id=admin.id, item_id=item2_user.id)
    await wishlist_controller.create_wish(wish2, admin)

    print("Database is now filled with fake data")


async def wipe_database(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    print("Database is now fully clear")


async def main():
    engine = await create_app_engine()
    await create_db_and_tables(engine)
    if len(sys.argv) == 2:
        if sys.argv[1] == "delete":
            await wipe_database(engine)
        elif sys.argv[1] == "create":
            async with AsyncSession(engine, expire_on_commit=False) as session:
                await create_data(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
