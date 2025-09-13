import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreditStatus(enum.Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"


class CreditSchema(BaseModel):
    amount: int
    expires_at: Optional[datetime] = None
    is_from_plan: bool = False
    status: CreditStatus

    class Config:
        from_attributes = True
        use_enum_values = True


class CreditAddSchema(BaseModel):
    amount: int
    expires_at: Optional[datetime] = None
    is_from_plan: bool = False


class BulkCreditAddSchema(BaseModel):
    """Schema for adding credits to multiple users in bulk."""

    amount: int
    expires_at: Optional[datetime] = None
    is_from_plan: bool = False  # Usually bulk credits might not be 'from plan'


def credit_to_schema(credit: "Credit") -> CreditSchema:  # type: ignore
    return CreditSchema(
        amount=credit.amount,
        expires_at=credit.expires_at,
        is_from_plan=credit.is_from_plan,
        status=credit.status,
    )
