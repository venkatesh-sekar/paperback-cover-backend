from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from paperback_cover.credit.schema import CreditStatus
from paperback_cover.models.base import Modifiable, Timestamped


class Credit(Timestamped, Modifiable):
    __tablename__ = "credit"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)
    amount: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[datetime] = mapped_column(nullable=True)
    is_from_plan: Mapped[bool] = mapped_column(default=False)
    status: Mapped[CreditStatus] = mapped_column(
        SQLAlchemyEnum(CreditStatus), default=CreditStatus.ACTIVE, index=True
    )
