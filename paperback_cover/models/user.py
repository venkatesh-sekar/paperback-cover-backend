import datetime
import enum
from typing import TYPE_CHECKING, List, Optional

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paperback_cover.credit.schema import CreditStatus
from paperback_cover.models.auth import OAuthAccount
from paperback_cover.models.base import Timestamped
from paperback_cover.models.credit import Credit
from paperback_cover.models.dodopayments import DodopaymentsUser

if TYPE_CHECKING:
    from paperback_cover.models.feedback import Feedback


class UserType(enum.Enum):
    BASE = "base"
    SUPERUSER = "superuser"
    ADMIN = "admin"


class User(SQLAlchemyBaseUserTableUUID, Timestamped):
    oauth_accounts: Mapped[List[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined"
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationship to DodopaymentsUser
    dodopayments_user: Mapped[Optional[DodopaymentsUser]] = relationship(
        "DodopaymentsUser", back_populates="user", uselist=False
    )

    # Relationship to upvoted feedback
    upvoted_feedback: Mapped[List["Feedback"]] = relationship(
        "Feedback", secondary="feedback_upvote_association", back_populates="upvoted_by"
    )

    credits: Mapped[List["Credit"]] = relationship(
        "Credit", cascade="all, delete-orphan", lazy="selectin"
    )

    def get_type(self) -> UserType:
        if self.is_superuser:
            return UserType.SUPERUSER
        return UserType.BASE

    @property
    def total_credits(self) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        return sum(
            credit.amount
            for credit in self.credits
            if credit.status.value == CreditStatus.ACTIVE.value
            and (
                credit.expires_at is None
                or credit.expires_at > now.replace(tzinfo=None)
            )
        )
