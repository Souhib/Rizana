

from rizana.api.models.item import BaseItem, CategoryBase


class ItemCreate(BaseItem):
    username: str
    email: str
    emirate_id: str
    password: str


class CategoryCreate(CategoryBase): ...
