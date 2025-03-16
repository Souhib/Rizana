from uuid import UUID

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.table import Category, Item, ItemCategoryLink, ItemImage
from rizana.api.schemas.error import (
    CategoryAlreadyExist,
    CategoryDoesNotExist,
    ItemDoesNotExist,
    ItemImageDoesNotExist,
    ItemsDependsOnCategory,
    NoLinkBetweenCategoryAndItem,
    UserNotAllowed,
    UserNotFoundError,
)
from rizana.api.schemas.item import CategoryCreate, ItemCreate


class ItemController:
    """
    Handles operations related to items, including creation, retrieval, and deletion.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the ItemController with a database session.

        Args:
            db (AsyncSession): The database session to use for operations.
        """
        self.db = db

    async def create_item(self, item_create: ItemCreate, user_id: UUID):
        """
        Creates a new item and associates it with the given user.

        Args:
            item_create (ItemCreate): The item creation schema.
            user_id (UUID): The ID of the user creating the item.

        Returns:
            Item: The newly created item object.
        """
        try:
            new_item = Item(
                **item_create.model_dump(exclude=("images", "categories")),
                user_id=user_id,
            )
            self.db.add(new_item)
            await self.db.commit()
            await self.db.refresh(new_item)
            for image_url in item_create.images:
                self.db.add(ItemImage(url=image_url, item_id=new_item.id))
            for category in item_create.categories:
                category_id = (await self.get_category(category)).id
                self.db.add(
                    ItemCategoryLink(item_id=new_item.id, category_id=category_id)
                )
            await self.db.commit()
            await self.db.refresh(new_item)
            return new_item
        except CategoryDoesNotExist as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_item(self, item_id: UUID, user_id: UUID) -> Item:
        """
        Retrieves an item by its ID.

        Args:
            item_id (UUID): The ID of the item to retrieve.
            user_id (UUID): The ID of the user attempting to retrieve the item.

        Returns:
            Item: The item object if found, otherwise raises ItemDoesNotExist.
        """
        item = (await self.db.exec(select(Item).where(Item.id == item_id))).first()
        if not item:
            raise ItemDoesNotExist(item_id=item_id)
        if item.user_id != user_id:
            raise UserNotAllowed(uuid=user_id, action="Get an item that is not yours")
        return item

    async def get_user_items(self, user_id: UUID):
        """
        Retrieves all items associated with a given user.

        Args:
            user_id (UUID): The ID of the user whose items to retrieve.

        Returns:
            list[Item]: A list of item objects associated with the user.
        """
        try:
            return (
                await self.db.exec(select(Item).where(Item.user_id == user_id))
            ).all()
        except NoResultFound as e:
            raise UserNotFoundError(user_id=user_id) from e

    async def delete_item(self, item_id: UUID, user_id: UUID):
        """
        Deletes an item and its associated images and categories.

        Args:
            item_id (UUID): The ID of the item to delete.
            user_id (UUID): The ID of the user attempting to delete the item.
        """
        try:
            item = (await self.db.exec(select(Item).where(Item.id == item_id))).one()
        except NoResultFound as e:
            raise ItemDoesNotExist(item_id=item_id) from e
        try:
            if item.user_id != user_id:
                raise UserNotAllowed(
                    uuid=user_id, action="delete an item that is not yours"
                )
            for image in item.images:
                item_image_link = await self._get_item_image(image.id)
                await self.db.delete(item_image_link)
            for category in item.categories:
                item_category_link = await self._get_item_category_link(
                    item_id=item.id, category_id=category.id
                )
                await self.db.delete(item_category_link)
            await self.db.delete(item)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def _get_item_image(self, image_id: UUID) -> ItemImage:
        """
        Retrieves an item image by its ID.

        Args:
            image_id (UUID): The ID of the item image to retrieve.

        Returns:
            ItemImage: The item image object if found, otherwise raises ItemImageDoesNotExist.
        """
        try:
            return (
                await self.db.exec(select(ItemImage).where(ItemImage.id == image_id))
            ).one()
        except NoResultFound as e:
            raise ItemImageDoesNotExist(image_id=image_id) from e

    async def _get_item_category_link(
        self, item_id: UUID, category_id: UUID
    ) -> ItemCategoryLink:
        """
        Retrieves the link between an item and a category.

        Args:
            item_id (UUID): The ID of the item.
            category_id (UUID): The ID of the category.

        Returns:
            ItemCategoryLink: The link object if found, otherwise raises NoLinkBetweenCategoryAndItem.
        """
        try:
            return (
                await self.db.exec(
                    select(ItemCategoryLink).where(
                        ItemCategoryLink.item_id == item_id,
                        ItemCategoryLink.category_id == category_id,
                    )
                )
            ).one()
        except NoResultFound as e:
            raise NoLinkBetweenCategoryAndItem(
                item_id=item_id, category_id=category_id
            ) from e

    async def get_category(self, category_name: str) -> Category:
        """
        Retrieves a category by its name.

        Args:
            category_name (str): The name of the category to retrieve.

        Returns:
            Category: The category object if found, otherwise raises CategoryDoesNotExist.
        """
        try:
            return (
                await self.db.exec(
                    select(Category).where(Category.name == category_name)
                )
            ).one()
        except NoResultFound as e:
            raise CategoryDoesNotExist(category_name=category_name) from e

    async def create_category(self, category_create: CategoryCreate):
        """
        Creates a new category.

        Args:
            category_create (CategoryCreate): The category creation schema.

        Returns:
            Category: The newly created category object.
        """
        try:
            new_category = Category(**category_create.model_dump())
            self.db.add(new_category)
            await self.db.commit()
            await self.db.refresh(new_category)
            return new_category
        except IntegrityError as e:
            await self.db.rollback()
            raise CategoryAlreadyExist(category_name=category_create.name) from e

    async def delete_category(self, category_name: str):
        """
        Deletes a category.

        Args:
            category_name (str): The name of the category to delete.
        """
        try:
            category = (
                await self.db.exec(
                    select(Category).where(Category.name == category_name)
                )
            ).one()
            await self.db.delete(category)
            await self.db.commit()
        except NoResultFound as e:
            raise CategoryDoesNotExist(category_name=category_name) from e
        except IntegrityError as e:
            await self.db.rollback()
            raise ItemsDependsOnCategory(category_name=category_name) from e
