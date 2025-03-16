import asyncio
import json
import random
import sys
from enum import Enum
from typing import List

import typer
from faker import Faker
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table
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
from rizana.api.schemas.payment import (
    BillingAddressCreate,
    CharityContributionCreate,
    PaymentMethodCreate,
)
from rizana.api.schemas.user import UserCreate, UserQuery
from rizana.api.schemas.wishlist import WishCreate
from rizana.api.services.stripe_service import StripeService
from rizana.database import create_app_engine, create_db_and_tables
from rizana.settings import Settings

app = typer.Typer()
console = Console()
faker = Faker()

logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


def log_section(title: str):
    """
    Print a formatted section header to the console.

    Args:
        title (str): The title text to display in the section header
    """
    console.print(Panel(title, style="bold blue", expand=False))


class DataType(Enum):
    ALL = "all"
    USERS = "users"
    CATEGORIES = "categories"
    ITEMS = "items"
    PAYMENTS = "payments"
    ORDERS = "orders"
    MESSAGES = "messages"
    WISHES = "wishes"
    CHARITY = "charity"


TEST_USERS = [
    {
        "username": "admin_user",
        "email": "admin@example.com",
        "password": "admin123",
        "emirate_id": "784-1234-1234567-1",
        "country": "ARE",
        "is_admin": True,
    },
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "john123",
        "emirate_id": "784-1234-1234567-2",
        "country": "ARE",
    },
    {
        "username": "jane_smith",
        "email": "jane@example.com",
        "password": "jane123",
        "emirate_id": "784-1234-1234567-3",
        "country": "ARE",
    },
]

TEST_CATEGORIES = [
    "Electronics",
    "Books",
    "Fashion",
    "Home & Garden",
    "Sports",
    "Toys",
    "Beauty",
    "Automotive",
]


async def create_users(user_controller: UserController) -> List[dict]:
    """
    Create test users with randomized data.

    Creates a mix of regular users with various attributes using Faker for data generation.
    Each user is created with basic profile information and authentication credentials.

    Args:
        user_controller (UserController): Controller instance for user operations

    Returns:
        List[dict]: List of created users with their details including IDs and emails

    Raises:
        Exception: If user creation fails, with error details logged
    """
    log_section("Creating Users")
    created_users = []

    for user_data in track(TEST_USERS, description="Creating users..."):
        try:
            is_admin = user_data.pop("is_admin", False)
            logger.info(f"Creating user: {user_data['email']}")

            user = await user_controller.create_user(UserCreate(**user_data))
            logger.debug(f"User created with ID: {user.id}")

            # Activate the user's account
            activation = await user_controller.get_user_activation(user.id)
            if activation:
                await user_controller.activate_user(user.id, activation.activation_key)
                logger.info(f"Activated account for: {user.email}")

            if is_admin:
                user = await user_controller.set_user_admin(user.id)
                logger.info(f"Granted admin privileges to: {user.email}")

            created_users.append(
                {"id": user.id, "email": user.email, "is_admin": user.is_admin}
            )
            console.print(
                f"[green]✓[/green] Created user: {user.email} ({'admin' if user.is_admin else 'user'})"
            )

        except Exception as e:
            logger.error(f"Failed to create user {user_data['email']}: {str(e)}")
            console.print(f"[red]✗[/red] Failed to create user: {user_data['email']}")

    return created_users


async def create_categories(item_controller: ItemController) -> List[dict]:
    """
    Create predefined test categories for items.

    Initializes the basic category structure for the marketplace with predefined
    category names and descriptions.

    Args:
        item_controller (ItemController): Controller instance for item operations

    Returns:
        List[dict]: List of created categories with their details

    Raises:
        Exception: If category creation fails, with error details logged
    """
    log_section("Creating Categories")
    created_categories = []

    for category_name in track(TEST_CATEGORIES, description="Creating categories..."):
        try:
            logger.info(f"Creating category: {category_name}")
            category = await item_controller.create_category(
                CategoryCreate(
                    name=category_name, description=f"Description for {category_name}"
                )
            )
            created_categories.append({"id": category.id, "name": category.name})
            console.print(f"[green]✓[/green] Created category: {category_name}")

        except Exception as e:
            logger.error(f"Failed to create category {category_name}: {str(e)}")
            console.print(f"[red]✗[/red] Failed to create category: {category_name}")

    return created_categories


async def create_items(
    item_controller: ItemController, users: List[dict], categories: List[dict]
) -> List[dict]:
    """
    Create test items with random attributes and assign them to users and categories.

    Generates items with varied prices, conditions, and descriptions, distributing them
    among existing users as sellers and categories.

    Args:
        item_controller (ItemController): Controller instance for item operations
        users (List[dict]): List of available users to assign as sellers
        categories (List[dict]): List of available categories to assign items to

    Returns:
        List[dict]: List of created items with their complete details

    Raises:
        Exception: If item creation fails, with error details logged
    """
    log_section("Creating Items")
    created_items = []

    for user in track(users, description="Creating items for users..."):
        logger.info(f"Creating items for user: {user['email']}")
        for i in range(2):
            try:
                category = categories[i % len(categories)]
                title = f"Item {i + 1} by {user['email']}"

                logger.debug(f"Creating item: {title}")
                item = await item_controller.create_item(
                    ItemCreate(
                        title=title,
                        description=f"Description for item {i + 1}",
                        price=faker.random_int(min=1000, max=100000)
                        / 100,  # Génère un prix entre 10.00 et 1000.00
                        images=[f"http://example.com/image{i + 1}.jpg"],
                        categories=[category["name"]],
                    ),
                    user["id"],
                )
                created_items.append(
                    {"id": item.id, "title": item.title, "seller_id": user["id"]}
                )
                console.print(f"[green]✓[/green] Created item: {title}")

            except Exception as e:
                logger.error(f"Failed to create item for {user['email']}: {str(e)}")
                console.print(
                    f"[red]✗[/red] Failed to create item for: {user['email']}"
                )

    return created_items


async def create_billing_addresses(
    payment_controller: PaymentController, users: List[dict]
) -> List[dict]:
    """
    Create test billing addresses for users.

    Generates realistic billing addresses for each user using Faker,
    with UAE-specific formatting and details.

    Args:
        payment_controller (PaymentController): Controller instance for payment operations
        users (List[dict]): List of users to create billing addresses for

    Returns:
        List[dict]: List of created billing addresses with their details

    Raises:
        Exception: If billing address creation fails, with error details logged
    """
    log_section("Creating Billing Addresses")
    created_addresses = []

    for i, user in enumerate(track(users, description="Creating billing addresses...")):
        try:
            logger.info(f"Creating billing address for user: {user['email']}")
            billing_address = await payment_controller.create_billing_address(
                BillingAddressCreate(
                    billing_street=f"{i + 1} Main St",
                    billing_city="Dubai",
                    billing_state="Dubai",
                    billing_country="ARE",
                    billing_postal_code=f"1000{i}",
                ),
                user["id"],
            )
            created_addresses.append({"id": billing_address.id, "user_id": user["id"]})
            console.print(
                f"[green]✓[/green] Created billing address for: {user['email']}"
            )
            logger.debug(f"Created billing address ID: {billing_address.id}")

        except Exception as e:
            logger.error(
                f"Failed to create billing address for user {user['email']}: {str(e)}"
            )
            console.print(
                f"[red]✗[/red] Failed to create billing address for: {user['email']}"
            )

    return created_addresses


async def create_payments(
    payment_controller: PaymentController, users: List[dict]
) -> List[dict]:
    """
    Create test payment methods for users.

    Generates test credit card information and payment methods for users,
    alternating between VISA and Mastercard types.

    Args:
        payment_controller (PaymentController): Controller instance for payment operations
        users (List[dict]): List of users to create payment methods for

    Returns:
        List[dict]: List of created payment methods with their details

    Raises:
        Exception: If payment method creation fails, with error details logged
    """
    log_section("Creating Payment Methods")
    created_payments = []

    for i, user in enumerate(track(users, description="Creating payment methods...")):
        try:
            logger.info(f"Creating payment method for user: {user['email']}")
            payment = await payment_controller.create_payment(
                PaymentMethodCreate(
                    card_type=CardType.VISA if i % 2 == 0 else CardType.MASTERCARD,
                    card_number=f"4111111111111{111 + i}",
                    expiry_date="12/25",
                    cvv="123",
                    holder_name=f"User {i + 1}",
                ),
                user["id"],
            )
            created_payments.append({"id": payment.id, "user_id": user["id"]})
            console.print(
                f"[green]✓[/green] Created {payment.card_type} payment method for: {user['email']}"
            )
            logger.debug(f"Created payment method ID: {payment.id}")

        except Exception as e:
            logger.error(
                f"Failed to create payment method for user {user['email']}: {str(e)}"
            )
            console.print(
                f"[red]✗[/red] Failed to create payment method for: {user['email']}"
            )

    return created_payments


async def create_orders(
    order_controller: OrderController, items: List[dict], users: List[dict]
) -> List[dict]:
    """
    Create test orders between buyers and sellers.

    Generates orders with complete payment information, billing details, and charity
    contributions, ensuring buyers are different from sellers for each item.

    Args:
        order_controller (OrderController): Controller instance for order operations
        items (List[dict]): Available items to create orders for
        users (List[dict]): Available users to act as buyers

    Returns:
        List[dict]: List of created orders with their complete details

    Raises:
        Exception: If order creation fails, with error details logged
    """
    log_section("Creating Orders")
    created_orders = []

    for i, item in enumerate(track(items, description="Creating orders...")):
        logger.info(f"Processing order for item: {item['title']}")

        # Find a buyer that is not the seller of this item
        potential_buyers = [u for u in users if u["id"] != item["seller_id"]]
        if not potential_buyers:
            logger.warning(f"No eligible buyers for item {item['id']}")
            console.print(
                f"[yellow]⚠[/yellow] Skipping order for item {item['id']}: No eligible buyers"
            )
            continue

        try:
            buyer_dict = potential_buyers[i % len(potential_buyers)]
            buyer = await order_controller.user_controller.get_user(
                UserQuery(user_id=buyer_dict["id"])
            )
            logger.debug(f"Selected buyer: {buyer.email} for item: {item['title']}")

            order = await order_controller.create_order(
                OrderCreate(
                    item_id=item["id"],
                    status=OrderStatus.PENDING,
                    payment_method=PaymentMethodCreate(
                        card_type=CardType.VISA if i % 2 == 0 else CardType.MASTERCARD,
                        card_number=f"4111111111111{111 + i}",
                        expiry_date="12/25",
                        cvv="123",
                        holder_name=f"User {i + 1}",
                    ),
                    billing_address=BillingAddressCreate(
                        billing_street=f"{i + 1} Main St",
                        billing_city="Dubai",
                        billing_state="Dubai",
                        billing_country="ARE",
                        billing_postal_code=f"1000{i}",
                    ),
                    charity_contribution=CharityContributionBase(
                        amount=5.0, is_rounded=i % 2 == 0
                    ),
                    save_card=False,
                    save_billing_address=False,
                ),
                buyer,
            )
            created_orders.append(
                {"id": order.id, "buyer_id": buyer.id, "seller_id": item["seller_id"]}
            )
            logger.info(
                f"Created order {order.id}: Buyer={buyer.email}, Item={item['title']}"
            )
            console.print(f"[green]✓[/green] Created order: {order.id}")

        except Exception as e:
            logger.error(f"Failed to create order for item {item['id']}: {str(e)}")
            console.print(
                f"[red]✗[/red] Failed to create order for item: {item['title']}"
            )

    return created_orders


async def create_messages(
    chat_controller: ChatController, users: List[dict], items: List[dict]
) -> List[dict]:
    """
    Create test chat messages between buyers and sellers.

    Generates conversations with multiple messages between users,
    including item inquiries and price negotiations.

    Args:
        chat_controller (ChatController): Controller instance for chat operations
        users (List[dict]): List of available users for conversations
        items (List[dict]): List of items to discuss in conversations

    Returns:
        List[dict]: List of created messages and conversations

    Raises:
        Exception: If message creation fails, with error details logged
    """
    log_section("Creating Messages")
    created_messages = []

    for item in track(
        items[:5], description="Creating messages..."
    ):  # Limit to 5 items for example
        try:
            seller_id = item["seller_id"]
            # Find a buyer that isn't the seller
            buyer = next((u for u in users if u["id"] != seller_id), None)
            if not buyer:
                continue

            # Create conversation
            conversation = await chat_controller.create_conversation(
                buyer["id"], seller_id, item["id"]
            )

            # Create initial message from buyer
            message1 = await chat_controller.send_message(
                buyer["id"],
                MessageCreate(
                    receiver_id=seller_id,
                    message=f"Hi! Is this item still available? {item['title']}",
                    conversation_id=conversation.id,
                ),
            )

            # Create seller response
            message2 = await chat_controller.send_message(
                seller_id,
                MessageCreate(
                    receiver_id=buyer["id"],
                    message="Yes, it's available! Are you interested?",
                    conversation_id=conversation.id,
                ),
            )

            # Create price proposal
            await chat_controller.create_proposal(
                buyer["id"],
                ProposalCreate(
                    item_id=item["id"],
                    proposed_price=90.0,
                    conversation_id=conversation.id,
                    receiver_id=seller_id,
                ),
            )

            created_messages.extend(
                [
                    {"id": message1.id, "conversation_id": conversation.id},
                    {"id": message2.id, "conversation_id": conversation.id},
                ]
            )
            console.print(
                f"[green]✓[/green] Created messages for item: {item['title']}"
            )

        except Exception as e:
            logger.error(f"Failed to create messages for item {item['id']}: {str(e)}")
            console.print(
                f"[red]✗[/red] Failed to create messages for item: {item['title']}"
            )

    return created_messages


async def create_wishes(
    wishlist_controller: WishlistController,
    user_controller: UserController,
    users: List[dict],
    items: List[dict],
) -> List[dict]:
    """
    Create test wishlist entries for users.

    Generates wishlist items for users, ensuring users don't wish for their own items.

    Args:
        wishlist_controller (WishlistController): Controller instance for wishlist operations
        user_controller (UserController): Controller instance for user operations
        users (List[dict]): List of users to create wishes for
        items (List[dict]): List of available items

    Returns:
        List[dict]: List of created wishlist entries

    Raises:
        Exception: If wish creation fails, with error details logged
    """
    log_section("Creating Wishes")
    created_wishes = []

    for user_dict in track(users, description="Creating wishes..."):
        # Get actual User object from controller
        user = await user_controller.get_user(UserQuery(user_id=user_dict["id"]))
        try:
            # Find items not owned by the user
            available_items = [item for item in items if item["seller_id"] != user.id]
            if not available_items:
                continue

            # Add 1-3 random items to wishlist
            for item in available_items[:3]:  # Limit to 3 wishes per user
                _ = await wishlist_controller.create_wish(
                    WishCreate(user_id=user.id, item_id=item["id"]),
                    user,
                )
                created_wishes.append({"user_id": user.id, "item_id": item["id"]})
                console.print(f"[green]✓[/green] Created wish for user: {user.email}")

        except Exception as e:
            logger.error(
                f"Failed to create wish for user {user_dict['email']}: {str(e)}"
            )
            console.print(
                f"[red]✗[/red] Failed to create wish for: {user_dict['email']}"
            )

    return created_wishes


async def create_charity_contributions(
    order_controller: OrderController, orders: List[dict]
) -> List[dict]:
    """
    Create test charity contributions for orders.

    Generates varied charity contribution amounts for existing orders,
    with a mix of rounded and exact amounts.

    Args:
        order_controller (OrderController): Controller instance for order operations
        orders (List[dict]): List of orders to add contributions to

    Returns:
        List[dict]: List of created charity contributions

    Raises:
        Exception: If contribution creation fails, with error details logged
    """
    log_section("Creating Charity Contributions")
    created_contributions = []

    for i, order in enumerate(
        track(orders, description="Creating charity contributions...")
    ):
        try:
            contribution = CharityContributionCreate(
                amount=round(random.uniform(1.0, 10.0), 2), is_rounded=i % 2 == 0
            )
            # Update order with charity contribution
            updated_order = await order_controller.update_order_charity(
                order["id"], contribution
            )
            created_contributions.append(
                {
                    "id": updated_order.id,
                    "amount": contribution.amount,
                    "is_rounded": contribution.is_rounded,
                }
            )
            console.print(
                f"[green]✓[/green] Created charity contribution for order: {order['id']}"
            )

        except Exception as e:
            logger.error(
                f"Failed to create charity contribution for order {order['id']}: {str(e)}"
            )
            console.print(
                f"[red]✗[/red] Failed to create charity contribution for order: {order['id']}"
            )

    return created_contributions


def print_payment_example_from_data(created_data: dict):
    """
    Generate and print a sample payment creation payload using actual database data.

    Creates a formatted example of a payment intent creation request using
    real item IDs from the database, useful for API testing.

    Args:
        created_data (dict): Dictionary containing created test data including items and users
    """
    if not created_data.get("items") or not created_data.get("users"):
        return

    # Get first item and a user who is not the seller
    item = created_data["items"][0]
    user = next(
        (u for u in created_data["users"] if u["id"] != item["seller_id"]), None
    )

    if not user:
        return

    payment_example = {
        "item_id": str(item["id"]),  # Convert UUID to string
        "payment_method": {
            "card_type": "VISA",
            "card_number": "4242424242424242",
            "expiry_date": "12/25",
            "cvv": "123",
            "holder_name": "Test User",
        },
        "billing_address": {
            "billing_street": "123 Main St",
            "billing_city": "Dubai",
            "billing_state": "Dubai",
            "billing_country": "ARE",
            "billing_postal_code": "12345",
        },
        "charity_contribution": {"amount": 5.0, "is_rounded": True},
        "save_card": True,
        "save_billing_address": True,
    }

    console.print(
        "\n[bold yellow]═══════════════════════════════════════[/bold yellow]"
    )
    console.print(
        "[bold green]Payment Creation Example with Database Data[/bold green]"
    )
    console.print("[bold yellow]═══════════════════════════════════════[/bold yellow]")
    console.print(
        "\nCopy this payload for Swagger POST /api/payments/create-payment-intent:"
    )
    console.print(json.dumps(payment_example, indent=2))
    console.print(
        "\n[bold blue]Note:[/bold blue] This uses actual item_id from your database"
    )
    console.print("[bold yellow]═══════════════════════════════════════[/bold yellow]")


async def create_data(db: AsyncSession, data_types: List[DataType] | None = None):
    """
    Create comprehensive test data based on specified data types.

    Orchestrates the creation of all types of test data including users, items,
    categories, payments, and orders. Handles controller initialization and
    sequential data creation with proper logging.

    Args:
        db (AsyncSession): Database session for all operations
        data_types (List[DataType] | None): Types of data to create, defaults to all types

    Returns:
        dict: Dictionary containing all created data organized by type

    Raises:
        Exception: If any part of data creation fails, with detailed error logging
    """

    log_section("Initializing Data Creation")
    settings = Settings()  # type: ignore
    if data_types is None:
        data_types = [DataType.ALL]
    created_data = {}

    try:
        # Initialize controllers
        logger.info("Initializing controllers")
        user_controller = UserController(
            db,
            settings.jwt_secret_key,
            settings.jwt_encryption_algorithm,
            settings.resend_api_key,
            settings.environment,
        )
        item_controller = ItemController(db)
        order_controller = OrderController(db, user_controller)
        stripe_service = StripeService(
            settings.stripe_secret_key,
            settings.frontend_success_url,
            settings.frontend_cancel_url,
        )
        payment_controller = PaymentController(db, stripe_service, order_controller)
        chat_controller = ChatController(
            db, user_controller, item_controller, order_controller
        )
        wishlist_controller = WishlistController(db)
        logger.debug("Controllers initialized successfully")

        # Create data based on specified types
        with console.status("[bold blue]Creating test data...") as status:
            if DataType.ALL in data_types or DataType.USERS in data_types:
                status.update("[bold blue]Creating users...")
                created_data["users"] = await create_users(user_controller)
                logger.info(f"Created {len(created_data['users'])} users")

            if DataType.ALL in data_types or DataType.CATEGORIES in data_types:
                status.update("[bold blue]Creating categories...")
                created_data["categories"] = await create_categories(item_controller)
                logger.info(f"Created {len(created_data['categories'])} categories")

            if DataType.ALL in data_types or DataType.ITEMS in data_types:
                status.update("[bold blue]Creating items...")
                created_data["items"] = await create_items(
                    item_controller,
                    created_data.get("users", []),
                    created_data.get("categories", []),
                )
                logger.info(f"Created {len(created_data['items'])} items")

            if DataType.ALL in data_types or DataType.PAYMENTS in data_types:
                status.update("[bold blue]Creating payments...")
                # First create billing addresses
                created_data["billing_addresses"] = await create_billing_addresses(
                    payment_controller, created_data.get("users", [])
                )
                logger.info(
                    f"Created {len(created_data['billing_addresses'])} billing addresses"
                )

                # Then create payment methods
                created_data["payments"] = await create_payments(
                    payment_controller, created_data.get("users", [])
                )
                logger.info(f"Created {len(created_data['payments'])} payment methods")

            if DataType.ALL in data_types or DataType.ORDERS in data_types:
                status.update("[bold blue]Creating orders...")
                created_data["orders"] = await create_orders(
                    order_controller,
                    created_data.get("items", []),
                    created_data.get("users", []),
                )
                logger.info(f"Created {len(created_data['orders'])} orders")

            if DataType.ALL in data_types or DataType.MESSAGES in data_types:
                status.update("[bold blue]Creating messages...")
                created_data["messages"] = await create_messages(
                    chat_controller,
                    created_data.get("users", []),
                    created_data.get("items", []),
                )
                logger.info(f"Created {len(created_data['messages'])} messages")

            if DataType.ALL in data_types or DataType.WISHES in data_types:
                status.update("[bold blue]Creating wishes...")
                created_data["wishes"] = await create_wishes(
                    wishlist_controller,
                    user_controller,  # Add user_controller here
                    created_data.get("users", []),
                    created_data.get("items", []),
                )
                logger.info(f"Created {len(created_data['wishes'])} wishes")

            if DataType.ALL in data_types or DataType.CHARITY in data_types:
                status.update("[bold blue]Creating charity contributions...")
                created_data["charity_contributions"] = (
                    await create_charity_contributions(
                        order_controller, created_data.get("orders", [])
                    )
                )
                logger.info(
                    f"Created {len(created_data['charity_contributions'])} charity contributions"
                )

        logger.success("All test data created successfully")
        # print_payment_example_from_data(created_data)
        return created_data

    except Exception as e:
        logger.error(f"Error during data creation: {str(e)}")
        console.print(f"[red]Error during data creation:[/red] {str(e)}")
        raise


async def wipe_database(engine: AsyncEngine):
    """
    Drop all tables from the database.

    Completely clears the database by dropping all tables, useful for
    clean slate testing or database reset.

    Args:
        engine (AsyncEngine): SQLAlchemy engine instance for database operations
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


def print_summary(data: dict):
    """
    Print a formatted summary of all created test data.

    Creates a rich console table showing counts and status for each type
    of data created during the initialization process.

    Args:
        data (dict): Dictionary containing all created test data organized by type
    """

    log_section("Creation Summary")

    table = Table(title="Created Data Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_column("Status", style="green")

    for data_type, items in data.items():
        count = len(items)
        status = "✓" if count > 0 else "✗"
        table.add_row(data_type, str(count), status)
        logger.info(f"Created {count} {data_type}")

    console.print(table)


@app.command()
def init(
    action: str = typer.Argument(
        "create", help="Action to perform: 'create' or 'delete'"
    ),
    data_types: List[str] = typer.Option(
        ["all"],
        "--data-types",
        "-t",
        help="Types of data to create (all, users, categories, items, payments, orders, messages, wishes, charity)",
    ),
    show_summary: bool = typer.Option(True, help="Show summary of created data"),
):
    """
    Initialize or clear the database with test data.

    Command-line interface for database operations, supporting creation of test data
    or complete database cleanup. Handles database connection, table creation,
    and orchestrates the entire initialization process.

    Args:
        action (str): The action to perform - either 'create' or 'delete'
        data_types (List[DataType]): Specific types of data to create
        show_summary (bool): Whether to display a summary after data creation

    Raises:
        Exception: If database initialization fails, with detailed error logging
    """

    try:
        enum_data_types = [DataType(dt.lower()) for dt in data_types]
    except ValueError:
        valid_types = ", ".join([t.value for t in DataType])
        console.print(f"[red]Invalid data type. Valid types are: {valid_types}[/red]")
        raise typer.Exit(1)

    logger.info(f"Starting database initialization - Action: {action}")

    async def run():
        try:
            engine = await create_app_engine()
            await create_db_and_tables(engine)
            logger.info("Database connection established")

            if action == "delete":
                await wipe_database(engine)
                logger.info("Database wiped clean")
            elif action == "create":
                async with AsyncSession(engine, expire_on_commit=False) as session:
                    data = await create_data(session, enum_data_types)
                    if show_summary:
                        print_summary(data)

            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
        await engine.dispose()

    asyncio.run(run())


if __name__ == "__main__":
    app()
