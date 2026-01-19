from typing import List
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.table import Wish
from rizana.api.schemas.error import (
    WishlistItemAlreadyExistsError,
    WishlistItemNotFoundError,
    WishlistItemNotOwnedError,
)
from rizana.api.schemas.wishlist import WishCreate, WishUpdate


class WishlistController:
    """Controller for managing wishlist operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the controller with a database session.

        Args:
            session: The database session to use.
        """
        self.session = session

    async def get_by_id(self, wishlist_id: int, user_id: UUID) -> Wish:
        """Get a wishlist item by ID.

        Args:
            wishlist_id: The ID of the wishlist item to retrieve.
            user_id: The ID of the user making the request.

        Returns:
            The wishlist item.

        Raises:
            WishlistItemNotFoundError: If the wishlist item is not found.
            WishlistItemNotOwnedError: If the user doesn't own the wishlist item.
        """
        result = await self.session.execute(
            select(Wish).where(Wish.id == wishlist_id)
        )
        wish = result.scalar_one_or_none()
        if not wish:
            raise WishlistItemNotFoundError(wishlist_id)
        if wish.user_id != user_id:
            raise WishlistItemNotOwnedError(user_id, wishlist_id)
        return wish

    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Wish]:
        """Get wishlist items for a user.

        Args:
            user_id: The ID of the user.
            skip: Number of items to skip.
            limit: Maximum number of items to return.

        Returns:
            List of wishlist items.
        """
        result = await self.session.execute(
            select(Wish)
            .where(Wish.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, wish_create: WishCreate, user_id: UUID) -> Wish:
        """Create a new wishlist item.

        Args:
            wish_create: The wishlist item data.
            user_id: The ID of the user creating the wishlist item.

        Returns:
            The created wishlist item.

        Raises:
            WishlistItemAlreadyExistsError: If the wishlist item already exists.
        """
        # Check if item already exists in wishlist
        result = await self.session.execute(
            select(Wish).where(
                Wish.user_id == user_id,
                Wish.item_id == wish_create.item_id
            )
        )
        if result.scalar_one_or_none():
            raise WishlistItemAlreadyExistsError(user_id, wish_create.item_id)

        wish = Wish(**wish_create.dict(), user_id=user_id)
        self.session.add(wish)
        await self.session.commit()
        await self.session.refresh(wish)
        return wish

    async def update(self, wishlist_id: int, wish_update: WishUpdate, user_id: UUID) -> Wish:
        """Update a wishlist item.

        Args:
            wishlist_id: The ID of the wishlist item to update.
            wish_update: The updated wishlist item data.
            user_id: The ID of the user updating the wishlist item.

        Returns:
            The updated wishlist item.

        Raises:
            WishlistItemNotFoundError: If the wishlist item is not found.
            WishlistItemNotOwnedError: If the user doesn't own the wishlist item.
        """
        wish = await self.get_by_id(wishlist_id, user_id)
        for field, value in wish_update.dict(exclude_unset=True).items():
            setattr(wish, field, value)
        self.session.add(wish)
        await self.session.commit()
        await self.session.refresh(wish)
        return wish

    async def delete(self, wishlist_id: int, user_id: UUID) -> None:
        """Delete a wishlist item.

        Args:
            wishlist_id: The ID of the wishlist item to delete.
            user_id: The ID of the user deleting the wishlist item.

        Raises:
            WishlistItemNotFoundError: If the wishlist item is not found.
            WishlistItemNotOwnedError: If the user doesn't own the wishlist item.
        """
        wish = await self.get_by_id(wishlist_id, user_id)
        await self.session.delete(wish)
        await self.session.commit()
