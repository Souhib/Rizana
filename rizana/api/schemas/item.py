from rizana.api.models.item import BaseItem, CategoryBase


class ItemCreate(BaseItem):
    images: list[str]
    categories: list[str]


class CategoryCreate(CategoryBase): ...
