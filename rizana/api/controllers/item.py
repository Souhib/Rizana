from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from rizana.api.models.table import Category, Item
from rizana.api.schemas.error import CategoryAlreadyExist, ItemsDependsOnCategory
from rizana.api.schemas.item import CategoryCreate, ItemCreate
from sqlalchemy.exc import IntegrityError


class ItemController:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_item(self, item_create: ItemCreate):
        new_item = Item(**item_create.model_dump())
        self.db.add(new_item)
        await self.db.commit()
        await self.db.refresh(new_item)
        return new_item

    async def create_category(self, category_create: CategoryCreate):
        try:
            new_category = Category(**category_create.model_dump())
            self.db.add(new_category)
            await self.db.commit()
            await self.db.refresh(new_category)
            return new_category
        except IntegrityError:
            raise CategoryAlreadyExist(category_name=category_create.name)

    async def delete_category(self, category_name: str):
        try:
            category = (
                await self.db.exec(
                    select(Category).where(Category.name == category_name)
                )
            ).one()
            await self.db.delete(category)
            await self.db.commit()
        except IntegrityError:
            raise ItemsDependsOnCategory(category_name=category_name)
