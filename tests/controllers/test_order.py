import random
from uuid import UUID

import pytest
from faker import Faker
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.item import ItemController
from rizana.api.controllers.order import OrderController
from rizana.api.controllers.payment import PaymentController
from rizana.api.controllers.user import UserController
from rizana.api.models.order import OrderStatus
from rizana.api.models.payment import CardType
from rizana.api.models.table import Order
from rizana.api.schemas.error import (ItemDoesNotExist, OrderNotFoundError,
                                      UserNotAllowed)
from rizana.api.schemas.order import OrderCreate
from rizana.api.schemas.payment import (BillingAddressCreate,
                                        PaymentMethodCreate)
from rizana.api.schemas.user import UserQuery
from tests.conftest import create_item, create_user


@pytest.mark.asyncio
async def test_create_order(
    order_controller: OrderController,
    user_controller: UserController,
    item_controller: ItemController,
    payment_controller: PaymentController,
    faker: Faker,
):
    # Create test data
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)

    card_type = random.choice(list(CardType))
    card_number = faker.credit_card_number()
    expiry_date = faker.credit_card_expire()
    cvv = faker.credit_card_security_code()
    holder_name = faker.name()

    # Create billing address data
    street = faker.street_address()
    city = faker.city()
    state = faker.state()
    country = faker.country_code(representation="alpha-3")
    postal_code = faker.postcode()

    # Create order
    order_create = OrderCreate(
        item_id=item.id,
        payment_method=PaymentMethodCreate(
            card_type=card_type,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            holder_name=holder_name,
        ),
        billing_address=BillingAddressCreate(
            billing_street=street,
            billing_city=city,
            billing_state=state,
            billing_country=country,
            billing_postal_code=postal_code,
        ),
    )

    order = await order_controller.create_order(order_create, buyer)

    # Basic order assertions
    assert isinstance(order, Order)
    assert order.id is not None
    assert order.created_at is not None
    assert order.status == OrderStatus.PENDING

    # Item related assertions
    assert order.item_id == item.id
    assert order.item.title == item.title
    assert order.item.description == item.description
    assert order.item.price == item.price

    # User related assertions
    assert order.buyer_id == buyer.id
    assert order.seller_id == seller.id
    assert order.buyer.username == buyer.username
    assert order.seller.username == seller.username

    # Payment method assertions
    assert order.payment_method is not None
    assert order.payment_method.card_type == card_type
    assert order.payment_method.card_number == card_number
    assert order.payment_method.expiry_date == expiry_date
    assert order.payment_method.cvv == cvv

    # Billing address assertions
    assert order.billing_address is not None
    assert order.billing_address.billing_street == street
    assert order.billing_address.billing_city == city
    assert order.billing_address.billing_state == state
    assert order.billing_address.billing_country == country
    assert order.billing_address.billing_postal_code == postal_code

    # Price assertions
    assert order.total_price == item.price
    assert order.total_price > 0
    assert isinstance(order.total_price, float)


@pytest.mark.asyncio
async def test_create_order_item_not_exist(
    order_controller: OrderController, user_controller: UserController, faker: Faker
):
    # Create test data
    buyer = await create_user(user_controller, faker)

    card_type = random.choice(list(CardType))
    card_number = faker.credit_card_number()
    expiry_date = faker.credit_card_expire()
    cvv = faker.credit_card_security_code()
    holder_name = faker.name()

    # Create billing address data
    street = faker.street_address()
    city = faker.city()
    state = faker.state()
    country = faker.country_code(representation="alpha-3")
    postal_code = faker.postcode()

    # Create order
    order_create = OrderCreate(
        item_id=UUID("00000000-0000-0000-0000-000000000000"),
        payment_method=PaymentMethodCreate(
            card_type=card_type,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            holder_name=holder_name,
        ),
        billing_address=BillingAddressCreate(
            billing_street=street,
            billing_city=city,
            billing_state=state,
            billing_country=country,
            billing_postal_code=postal_code,
        ),
    )

    with pytest.raises(ItemDoesNotExist):
        await order_controller.create_order(order_create, buyer)


@pytest.mark.asyncio
async def test_create_order_buyer_is_seller(
    order_controller: OrderController,
    user_controller: UserController,
    item_controller: ItemController,
    payment_controller: PaymentController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    item = await create_item(item_controller, faker, user_id=buyer.id)

    card_type = random.choice(list(CardType))
    card_number = faker.credit_card_number()
    expiry_date = faker.credit_card_expire()
    cvv = faker.credit_card_security_code()
    holder_name = faker.name()

    # Create billing address data
    street = faker.street_address()
    city = faker.city()
    state = faker.state()
    country = faker.country_code(representation="alpha-3")
    postal_code = faker.postcode()

    # Create order
    order_create = OrderCreate(
        item_id=item.id,
        payment_method=PaymentMethodCreate(
            card_type=card_type,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            holder_name=holder_name,
        ),
        billing_address=BillingAddressCreate(
            billing_street=street,
            billing_city=city,
            billing_state=state,
            billing_country=country,
            billing_postal_code=postal_code,
        ),
    )
    with pytest.raises(UserNotAllowed):
        await order_controller.create_order(order_create, buyer)


@pytest.mark.asyncio
async def test_get_order_by_id(
    order_controller: OrderController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    # Create initial order
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)

    order_create = OrderCreate(
        item_id=item.id,
        payment_method=PaymentMethodCreate(
            card_type=random.choice(list(CardType)),
            card_number=faker.credit_card_number(),
            expiry_date=faker.credit_card_expire(),
            cvv=faker.credit_card_security_code(),
            holder_name=faker.name(),
        ),
        billing_address=BillingAddressCreate(
            billing_street=faker.street_address(),
            billing_city=faker.city(),
            billing_state=faker.state(),
            billing_country=faker.country_code(representation="alpha-3"),
            billing_postal_code=faker.postcode(),
        ),
    )

    created_order = await order_controller.create_order(order_create, buyer)
    retrieved_order = await order_controller.get_order(created_order.id)

    assert retrieved_order.id == created_order.id
    assert retrieved_order.status == created_order.status
    assert retrieved_order.total_price == created_order.total_price


@pytest.mark.asyncio
async def test_get_order_not_found(order_controller: OrderController):
    with pytest.raises(OrderNotFoundError):
        await order_controller.get_order(UUID("00000000-0000-0000-0000-000000000000"))


@pytest.mark.asyncio
async def test_get_user_orders(
    order_controller: OrderController,
    user_controller: UserController,
    item_controller: ItemController,
    session: AsyncSession,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())

    # Create multiple orders
    orders_count = 3
    for _ in range(orders_count):
        item = await create_item(item_controller, faker, user_id=seller.id)
        order_create = OrderCreate(
            item_id=item.id,
            payment_method=PaymentMethodCreate(
                card_type=random.choice(list(CardType)),
                card_number=faker.credit_card_number(),
                expiry_date=faker.credit_card_expire(),
                cvv=faker.credit_card_security_code(),
                holder_name=faker.name(),
            ),
            billing_address=BillingAddressCreate(
                billing_street=faker.street_address(),
                billing_city=faker.city(),
                billing_state=faker.state(),
                billing_country=faker.country_code(representation="alpha-3"),
                billing_postal_code=faker.postcode(),
            ),
        )
        await order_controller.create_order(order_create, buyer)

    await session.close()

    buyer = await user_controller.get_user(UserQuery(user_id=buyer.id))
    seller = await user_controller.get_user(UserQuery(user_id=seller.id))

    assert len(buyer.orders) == orders_count
    assert len(seller.sales) == orders_count
    assert all(isinstance(order, Order) for order in buyer.orders)
    assert all(order.buyer_id == buyer.id for order in buyer.orders)
    assert all(order.seller_id == seller.id for order in seller.sales)


@pytest.mark.asyncio
async def test_cancel_order_success(
    order_controller: OrderController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)

    order_create = OrderCreate(
        item_id=item.id,
        payment_method=PaymentMethodCreate(
            card_type=random.choice(list(CardType)),
            card_number=faker.credit_card_number(),
            expiry_date=faker.credit_card_expire(),
            cvv=faker.credit_card_security_code(),
            holder_name=faker.name(),
        ),
        billing_address=BillingAddressCreate(
            billing_street=faker.street_address(),
            billing_city=faker.city(),
            billing_state=faker.state(),
            billing_country=faker.country_code(representation="alpha-3"),
            billing_postal_code=faker.postcode(),
        ),
    )

    order = await order_controller.create_order(order_create, buyer)
    cancelled_order = await order_controller.cancel_order(
        order.id, buyer.id, "Changed my mind"
    )

    assert cancelled_order.status == OrderStatus.CANCELED
    cancellation = await order_controller.get_cancellation(order.id)
    assert cancellation.cancellation_reason == "Changed my mind"
    assert cancellation.user_id == buyer.id
    assert cancellation.order_id == order.id


@pytest.mark.asyncio
async def test_cancel_order_not_owner(
    order_controller: OrderController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    other_user = await create_user(user_controller, faker, email="other@example.com")
    item = await create_item(item_controller, faker, user_id=seller.id)

    order_create = OrderCreate(
        item_id=item.id,
        payment_method=PaymentMethodCreate(
            card_type=random.choice(list(CardType)),
            card_number=faker.credit_card_number(),
            expiry_date=faker.credit_card_expire(),
            cvv=faker.credit_card_security_code(),
            holder_name=faker.name(),
        ),
        billing_address=BillingAddressCreate(
            billing_street=faker.street_address(),
            billing_city=faker.city(),
            billing_state=faker.state(),
            billing_country=faker.country_code(representation="alpha-3"),
            billing_postal_code=faker.postcode(),
        ),
    )

    order = await order_controller.create_order(order_create, buyer)
    with pytest.raises(UserNotAllowed):
        await order_controller.cancel_order(order.id, other_user.id, "Not my order")


@pytest.mark.asyncio
async def test_create_order_with_expired_card(
    order_controller: OrderController,
    user_controller: UserController,
    item_controller: ItemController,
    faker: Faker,
):
    buyer = await create_user(user_controller, faker)
    seller = await create_user(user_controller, faker, email=faker.email())
    item = await create_item(item_controller, faker, user_id=seller.id)

    with pytest.raises(ValueError):
        order_create = OrderCreate(
            item_id=item.id,
            payment_method=PaymentMethodCreate(
                card_type=random.choice(list(CardType)),
                card_number=faker.credit_card_number(),
                expiry_date="01/20",  # Expired card
                cvv=faker.credit_card_security_code(),
                holder_name=faker.name(),
            ),
            billing_address=BillingAddressCreate(
                billing_street=faker.street_address(),
                billing_city=faker.city(),
                billing_state=faker.state(),
                billing_country=faker.country_code(representation="alpha-3"),
                billing_postal_code=faker.postcode(),
            ),
        )
        await order_controller.create_order(order_create, buyer)
