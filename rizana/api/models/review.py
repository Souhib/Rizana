from sqlmodel import Field

from rizana.api.models.shared import DBModel


class ReviewBase(DBModel):
    rating: int = Field(default=5)
    comment: str | None = Field(default=None, max_length=1000)
