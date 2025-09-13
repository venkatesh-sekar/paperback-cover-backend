from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paperback_cover.feedback.schema import FeedbackSchema

if TYPE_CHECKING:

    from paperback_cover.models.user import User

from paperback_cover.feedback.schema import (
    FeedbackPriority,
    FeedbackStatus,
    FeedbackType,
)
from paperback_cover.models.base import Base, Modifiable, UserGenerated

# Association table for feedback upvotes
feedback_upvote_association = Table(
    "feedback_upvote_association",
    Base.metadata,
    Column(
        "feedback_id",
        PostgresUUID(as_uuid=True),
        ForeignKey("feedback.id"),
        primary_key=True,
    ),
    Column(
        "user_id", PostgresUUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    ),
)


class Feedback(UserGenerated, Modifiable):
    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    feedback_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="open")
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    upvoted_by: Mapped[list["User"]] = relationship(
        "User", secondary=feedback_upvote_association, back_populates="upvoted_feedback"
    )

    def to_pydantic(self, current_user_id: Optional[UUID] = None) -> "FeedbackSchema":

        upvote_count = len(self.upvoted_by) if self.upvoted_by else 0
        user_has_upvoted = False
        if current_user_id and self.upvoted_by:
            user_has_upvoted = any(
                user.id == current_user_id for user in self.upvoted_by
            )

        return FeedbackSchema(
            id=self.id,
            subject=self.subject,
            message=self.message,
            feedback_type=FeedbackType(self.feedback_type),
            status=FeedbackStatus(self.status),
            priority=FeedbackPriority(self.priority),
            upvote_count=upvote_count,
            user_has_upvoted=user_has_upvoted,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
