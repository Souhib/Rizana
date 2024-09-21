from datetime import datetime
from enum import Enum

from sqlmodel import Field

from rizana.api.models.shared import DBModel


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class TransactionHistoryBase(DBModel):
    amount: float
    transaction_type: TransactionType
    transaction_date: datetime = Field(default_factory=datetime.now)
    status: TransactionStatus
