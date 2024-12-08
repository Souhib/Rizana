from typing import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.table import Item, User, Wish
from rizana.api.schemas.error import (ItemAlreadyInWishList, ItemDoesNotExist,
                                      UserCantAddHisOwnItemToWishlist,
                                      WishDoesNotExists)
from rizana.api.schemas.wishlist import WishCreate


class WishlistController:
    """
    Controller for managing user wishlists.

    This class provides methods for creating, removing, and retrieving items from a user's wishlist.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the WishlistController with a database session.

        Args:
            db (AsyncSession): The database session to use for operations.
        """
        self.db = db

    async def create_wish(self, wish_create: WishCreate, current_user: User):
        """
        Adds an item to the current user's wishlist.

        This method attempts to add an item to the current user's wishlist. If the item is already in the wishlist,
        it raises an ItemAlreadyInWishList error. If the item does not exist, it raises an ItemDoesNotExist error.
        If the current user is trying to add their own item to the wishlist, it raises a UserCantAddHisOwnItemToWishlist error.

        Args:
            wish_create (WishCreate): The item to add to the wishlist.
            current_user (User): The user adding the item to their wishlist.

        Returns:
            Wish: The newly created wishlist entry.

        Raises:
            ItemAlreadyInWishList: If the item is already in the wishlist.
            ItemDoesNotExist: If the item does not exist.
            UserCantAddHisOwnItemToWishlist: If the current user is trying to add their own item to the wishlist.
        """
        try:
            item = (
                await self.db.exec(select(Item).where(Item.id == wish_create.item_id))
            ).one()
            if item.user_id == current_user.id:
                raise UserCantAddHisOwnItemToWishlist(
                    item_id=item.id, username=current_user.username
                )
            new_wish = Wish(user_id=current_user.id, item_id=wish_create.item_id)
            self.db.add(new_wish)
            await self.db.commit()
            await self.db.refresh(new_wish)
            return new_wish
        except IntegrityError as e:
            await self.db.rollback()
            raise ItemAlreadyInWishList(
                item_id=wish_create.item_id, user_id=wish_create.user_id
            ) from e
        except NoResultFound as e:
            raise ItemDoesNotExist(item_id=wish_create.item_id) from e

    async def remove_wish(self, item_id: UUID, user_id: UUID):
        """
        Removes an item from a user's wishlist.

        This method attempts to remove an item from a user's wishlist. If the item does not exist in the wishlist,
        it raises a WishDoesNotExists error.

        Args:
            item_id (UUID): The ID of the item to remove from the wishlist.
            user_id (UUID): The ID of the user whose wishlist to modify.

        Raises:
            WishDoesNotExists: If the item does not exist in the wishlist.
        """
        try:
            wish = (
                await self.db.exec(
                    select(Wish)
                    .where(Wish.user_id == user_id)
                    .where(Wish.item_id == item_id)
                )
            ).one()
            await self.db.delete(wish)
            await self.db.commit()
        except NoResultFound:
            raise WishDoesNotExists(item_id=item_id, user_id=user_id)
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_wishlist(self, user_id: UUID) -> Sequence[Item]:
        """
        Retrieves the items in a user's wishlist.

        This method fetches all items in a user's wishlist.

        Args:
            user_id (UUID): The ID of the user whose wishlist to retrieve.

        Returns:
            list[Item]: A list of items in the user's wishlist.
        """
        return (
            await self.db.exec(
                select(Item)
                .join(Wish)
                .where(Item.id == Wish.item_id)
                .where(Wish.user_id == user_id)
            )
        ).all()
