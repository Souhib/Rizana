import random

from pydantic import ConfigDict
from sqlmodel import SQLModel


class DBModel(SQLModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, arbitrary_types_allowed=True
    )  # type: ignore


def generate_activation_key() -> str:
    return "".join(random.choices("0123456789", k=5))
