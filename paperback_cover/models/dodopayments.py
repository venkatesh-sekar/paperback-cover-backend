from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paperback_cover.models.base import Modifiable, Timestamped

if TYPE_CHECKING:
    from paperback_cover.models.user import User


class DodopaymentsUser(Timestamped, Modifiable):
    __tablename__ = "dodopayments_user"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    dodopayments_customer_id: Mapped[str] = mapped_column(
        "dodopayments_customer_id", String(100), unique=True
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="dodopayments_user")
