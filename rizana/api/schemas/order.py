from datetime import datetime
from uuid import UUID

from rizana.api.models.order import CharityContributionBase, OrderBase
from rizana.api.models.payment import BillingAddressBase, PaymentMethodBase
from rizana.api.models.table import Item, User


class OrderCreate(OrderBase):
    charity_contribution: CharityContributionBase | None = None
    payment_method: PaymentMethodBase
    billing_address: BillingAddressBase
    save_card: bool = False
    save_billing_address: bool = False


class OrderView(OrderBase):
    id: UUID
    buyer_id: UUID
    seller_id: UUID
    created_at: datetime

    # Relationships
    item: Item
    buyer: User
    seller: User
