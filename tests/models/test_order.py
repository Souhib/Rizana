import random
from uuid import uuid4

import pytest
from faker import Faker

from rizana.api.models.order import OrderStatus
from rizana.api.models.payment import CardType
from rizana.api.schemas.order import OrderCreate
from rizana.api.schemas.payment import (BillingAddressCreate,
                                        PaymentMethodCreate)


@pytest.mark.asyncio
async def test_order_create_valid(faker: Faker):
    item_id = uuid4()
    order_create = OrderCreate(
        item_id=item_id,
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
    assert order_create.item_id == item_id
    assert order_create.status == OrderStatus.PENDING
