import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackType(enum.Enum):
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"


class FeedbackStatus(enum.Enum):
    OPEN = "open"
    REVIEWED = "reviewed"
    CLOSED = "closed"


class FeedbackPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FeedbackCreateSchema(BaseModel):
    subject: str = Field(
        ..., min_length=1, max_length=200, description="Subject of the feedback"
    )
    message: str = Field(..., min_length=1, description="Detailed feedback message")
    feedback_type: FeedbackType = Field(
        ...,
        description="Type of feedback: bug, feature_request, or general",
    )
    priority: FeedbackPriority = Field(
        default=FeedbackPriority.MEDIUM,
        description="Priority level: low, medium, or high",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Issue with book cover generation",
                "message": "The cover generation process is taking too long and sometimes fails.",
                "feedback_type": "bug",
                "priority": "high",
            }
        }


class FeedbackUpdateSchema(BaseModel):
    message: Optional[str] = Field(None, min_length=1)


class FeedbackSchema(BaseModel):
    id: UUID
    subject: str
    message: str
    feedback_type: FeedbackType
    status: FeedbackStatus
    priority: FeedbackPriority
    upvote_count: int = Field(default=0, description="Number of upvotes")
    user_has_upvoted: bool = Field(
        default=False, description="Whether current user has upvoted"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackUpvoteSchema(BaseModel):
    feedback_id: UUID
    user_has_upvoted: bool
    upvote_count: int
