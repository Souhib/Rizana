from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.controllers.user import UserController
from rizana.api.models.order import OrderStatus
from rizana.api.models.table import (
    BillingAddress,
    CharityContribution,
    Conversation,
    Item,
    Order,
    OrderCancellation,
    PaymentMethod,
    Proposal,
    User,
)
from rizana.api.schemas.chat import ProposalStatus
from rizana.api.schemas.error import (
    ItemDoesNotExist,
    OrderNotFoundError,
    UserNotAllowed,
)
from rizana.api.schemas.order import OrderCreate
from rizana.api.schemas.payment import CharityContributionCreate
from rizana.api.schemas.user import UserQuery


class OrderController:
    """
    Handles operations related to orders, including creation and association with users.
    """

    def __init__(self, db: AsyncSession, user_controller: UserController):
        """
        Initializes the OrderController with a database session and a user controller.

        Args:
            db (AsyncSession): The database session to use for operations.
            user_controller (UserController): The controller for user-related operations.
        """
        self.db = db
        self.user_controller = user_controller

    async def create_order(self, order_create: OrderCreate, current_user: User):
        """
        Creates a new order and associates it with the buyer and seller users. Optionally, it also creates a charity contribution.

        Args:
            order_create (OrderCreate): The order creation schema.
            current_user (User): The user creating the order.

        Returns:
            Order: The newly created order object.
        """
        # Get item
        item = (
            await self.db.exec(select(Item).where(Item.id == order_create.item_id))  # type: ignore
        ).first()
        if not item:
            raise ItemDoesNotExist(item_id=order_create.item_id)

        # Get buyer and seller
        buyer = current_user

        seller = await self.user_controller.get_user(UserQuery(user_id=item.user_id))

        if buyer.id == item.user_id:
            raise UserNotAllowed(
                uuid=buyer.id, action="Create an order for its own item"
            )

        price = (
            await self._get_accepted_proposal_price(order_create, buyer.id, seller.id)
            or item.price
        )

        # if order_create.save_card:
        payment_method = await self._save_payment_method(
            order_create.payment_method, buyer.id
        )

        # if order_create.save_billing_address:
        billing_address = await self._save_billing_address(
            order_create.billing_address, buyer.id
        )

        order = Order(
            **order_create.model_dump(
                exclude={"charity_contribution", "payment_method", "billing_address"}
            ),
            total_price=price,
            payment_method_id=payment_method.id,
            billing_address_id=billing_address.id,
            buyer_id=buyer.id,
            seller_id=seller.id,
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        if order_create.charity_contribution:
            await self._add_charity_contribution(
                order, order_create.charity_contribution
            )

        return order

    async def _get_accepted_proposal_price(
        self, order_create: OrderCreate, buyer_id: UUID, seller_id: UUID
    ) -> float | None:
        """
        Retrieves the price of an accepted proposal for a given order creation.

        This method queries the database to find a conversation related to the given buyer, seller, and item.
        If a conversation is found, it then queries for a proposal within that conversation that has been accepted.
        The price of the accepted proposal is returned if found, otherwise, None is returned.

        Args:
            order_create (OrderCreate): The order creation schema containing the item ID.
            buyer_id (UUID): The ID of the buyer.
            seller_id (UUID): The ID of the seller.

        Returns:
            float | None: The price of the accepted proposal or None if not found.
        """
        conversation = (
            await self.db.exec(
                select(Conversation).where(  # type: ignore
                    Conversation.buyer_id == buyer_id,
                    Conversation.seller_id == seller_id,
                    Conversation.item_id == order_create.item_id,
                )
            )
        ).first()

        if not conversation:
            return None

        proposal = (
            await self.db.exec(
                select(Proposal).where(  # type: ignore
                    Proposal.conversation_id == conversation.id,
                    Proposal.status == ProposalStatus.ACCEPTED,
                )
            )
        ).first()

        return proposal.proposed_price if proposal else None  # type: ignore

    async def _add_charity_contribution(self, order: Order, charity_data):
        """
        Adds a charity contribution to an order.

        This method creates a new CharityContribution object with the given data and associates it with the given order.
        It then saves the contribution to the database.

        Args:
            order (Order): The order to which the charity contribution is being added.
            charity_data: The data for the charity contribution.
        """
        contribution = CharityContribution(
            order_id=order.id,
            user_id=order.buyer_id,
            amount=charity_data.amount,
            is_rounded=charity_data.is_rounded,
        )
        self.db.add(contribution)
        await self.db.commit()
        await self.db.refresh(contribution)

    async def _save_payment_method(
        self, payment_method_data, user_id: UUID
    ) -> PaymentMethod:
        """
        Saves a payment method for a user.

        This method creates a new PaymentMethod object with the given data and associates it with the given user.
        It then saves the payment method to the database and returns the saved object.

        Args:
            payment_method_data: The data for the payment method.
            user_id (UUID): The ID of the user.

        Returns:
            PaymentMethod: The saved payment method object.
        """
        payment_method = PaymentMethod(
            **payment_method_data.model_dump(), user_id=user_id
        )
        self.db.add(payment_method)
        await self.db.commit()
        await self.db.refresh(payment_method)
        return payment_method

    async def _save_billing_address(
        self, billing_address_data, user_id: UUID
    ) -> BillingAddress:
        """
        Saves a billing address for a user.

        This method creates a new BillingAddress object with the given data and associates it with the given user.
        It then saves the billing address to the database and returns the saved object.

        Args:
            billing_address_data: The data for the billing address.
            user_id (UUID): The ID of the user.

        Returns:
            BillingAddress: The saved billing address object.
        """
        billing_address = BillingAddress(
            **billing_address_data.model_dump(), user_id=user_id
        )
        self.db.add(billing_address)
        await self.db.commit()
        await self.db.refresh(billing_address)
        return billing_address

    async def get_order(self, order_id: UUID) -> Order:
        """
        Retrieves an order by its ID.

        This method queries the database for an order with the given ID and returns the order object if found.

        Args:
            order_id (UUID): The ID of the order to retrieve.

        Returns:
            Order: The retrieved order object.
        """
        order = (await self.db.exec(select(Order).where(Order.id == order_id))).first()  # type: ignore
        if not order:
            raise OrderNotFoundError(order_id=order_id)
        return order

    async def cancel_order(self, order_id: UUID, user_id: UUID, reason: str):
        """
        Cancels an order.

        This method retrieves an order by its ID and checks if the user ID matches the buyer ID of the order.
        If the user is allowed to cancel the order, it updates the order status to cancelled and sets the cancellation reason.
        The updated order object is then returned.

        Args:
            order_id (UUID): The ID of the order to cancel.
            user_id (UUID): The ID of the user attempting to cancel the order.
            reason (str): The reason for cancelling the order.

        Returns:
            Order: The updated order object.
        """
        order = await self.get_order(order_id)
        if user_id != order.buyer_id:
            raise UserNotAllowed(
                uuid=order.buyer_id, action="cancel an order for another user"
            )
        order.status = OrderStatus.CANCELED
        cancellation = OrderCancellation(
            order_id=order.id, user_id=user_id, cancellation_reason=reason
        )
        self.db.add(cancellation)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_cancellations(self, user_id: UUID):
        """
        Retrieves all cancellations for a user.
        """
        return (
            await self.db.exec(
                select(OrderCancellation).where(OrderCancellation.user_id == user_id)  # type: ignore
            )
        ).all()

    async def get_cancellation(self, order_id: UUID):
        """
        Retrieves a cancellation by its order ID.
        """
        return (
            await self.db.exec(
                select(OrderCancellation).where(OrderCancellation.order_id == order_id)  # type: ignore
            )
        ).one()

    async def update_order_charity(
        self, order_id: UUID, charity_data: CharityContributionCreate
    ) -> Order:
        """
        Updates or adds a charity contribution to an existing order.

        Args:
            order_id (UUID): The ID of the order to update
            charity_data (CharityContributionBase): The charity contribution data

        Returns:
            Order: The updated order object

        Raises:
            OrderNotFoundError: If the order with the given ID doesn't exist
        """
        order = await self.get_order(order_id)

        # Add new charity contribution
        contribution = CharityContribution(
            order_id=order.id,
            user_id=order.buyer_id,
            amount=charity_data.amount,
            is_rounded=charity_data.is_rounded,
        )
        self.db.add(contribution)
        await self.db.commit()
        await self.db.refresh(order)

        return order
