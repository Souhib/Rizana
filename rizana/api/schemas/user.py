import re
from typing import Self
from uuid import UUID

from pydantic import model_validator

from rizana.api.models.shared import DBModel
from rizana.api.models.user import UserBase


class UserCreate(UserBase):
    password: str

class UserQuery(DBModel):
    user_id: UUID | None = None
    username: str | None = None
    email: str | None = None
    emirate_id: str | None = None

    @model_validator(mode="after")
    def check_that_at_least_one_param_is_set(self) -> Self:
        if not (self.email or self.username or self.email or self.emirate_id):
            raise ValueError(
                "At least one of user_id, username, email, or emirate_id must be provided"
            )
        return self


class UserView(UserBase): ...
