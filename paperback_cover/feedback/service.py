import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import func
from sqlalchemy import select as sql_select
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from paperback_cover.commons.db import get_async_session
from paperback_cover.credit.schema import CreditAddSchema
from paperback_cover.credit.service import add_credits
from paperback_cover.feedback.schema import (
    FeedbackCreateSchema,
    FeedbackSchema,
    FeedbackStatus,
    FeedbackUpdateSchema,
    FeedbackUpvoteSchema,
)
from paperback_cover.models.feedback import Feedback as FeedbackModel
from paperback_cover.models.feedback import feedback_upvote_association
from paperback_cover.models.user import User

logger = logging.getLogger(__name__)


async def create_feedback(
    feedback_data: FeedbackCreateSchema, user: User
) -> Optional[FeedbackSchema]:
    """Create a new feedback entry"""
    async with get_async_session() as session:
        feedback_id = uuid4()

        feedback_model = FeedbackModel(
            id=feedback_id,
            subject=feedback_data.subject,
            message=feedback_data.message,
            feedback_type=feedback_data.feedback_type.value,
            priority=feedback_data.priority.value,
            owner=user.id,
            user_id=user.id,
            status=FeedbackStatus.OPEN.value,
        )

        session.add(feedback_model)
        await session.commit()

        # Refresh the object to ensure it's properly attached to the session
        await session.refresh(feedback_model, ["upvoted_by"])

        logger.info(f"User {user.id} created feedback: {feedback_data.subject}")

        # Give user 10 credits for providing feedback
        try:
            credit_data = CreditAddSchema(amount=10, is_from_plan=False)
            await add_credits(user, credit_data)
            logger.info(f"Added 10 credits to user {user.id} for creating feedback")
        except Exception as e:
            logger.error(f"Failed to add credits to user {user.id}: {e}")
            # Don't fail the feedback creation if credit addition fails

        return feedback_model.to_pydantic(current_user_id=user.id)


async def update_feedback(
    feedback_id: UUID, feedback_data: FeedbackUpdateSchema, user: User
) -> Optional[FeedbackSchema]:
    """Update an existing feedback entry"""
    async with get_async_session() as session:
        feedback_model = await fetch_feedback_model_by_id(feedback_id)
        if not feedback_model or not feedback_model.is_authorised(user):
            logger.error(f"Feedback not found or unauthorized for user: {user.id}")
            return None

        if feedback_data.message is not None:
            feedback_model.message = feedback_data.message

        session.add(feedback_model)
        await session.commit()

        logger.info(f"User {user.id} updated feedback: {feedback_id}")

        # Refresh the object to ensure it's properly attached to the session
        await session.refresh(feedback_model, ["upvoted_by", "updated_at"])

        return feedback_model.to_pydantic(current_user_id=user.id)


async def get_feedback(feedback_id: UUID, user: User) -> Optional[FeedbackSchema]:
    """Get a specific feedback entry"""
    async with get_async_session() as session:
        query = select(FeedbackModel).where(FeedbackModel.id == feedback_id)
        query = query.options(selectinload(FeedbackModel.upvoted_by))
        result = await session.execute(query)
        feedback_model = result.scalar_one_or_none()

        if not feedback_model or not feedback_model.is_authorised(user):
            return None

        return feedback_model.to_pydantic(current_user_id=user.id)


async def get_user_feedback(user: User) -> Page[FeedbackSchema]:
    """Get all feedback entries for a user"""
    async with get_async_session() as session:
        query = select(FeedbackModel).where(FeedbackModel.owner == user.id)
        query = query.options(selectinload(FeedbackModel.upvoted_by))
        query = query.order_by(FeedbackModel.created_at.desc())

        return await paginate(
            conn=session,
            query=query,
            transformer=lambda x: [
                feedback.to_pydantic(current_user_id=user.id) for feedback in x
            ],
        )


async def get_all_feedback(user: User) -> Page[FeedbackSchema]:
    """Get all feedback entries (admin only)"""
    if not user.is_superuser:
        logger.warning(f"Non-admin user {user.id} attempted to access all feedback")
        return Page(items=[], total=0, page=1, size=50)

    async with get_async_session() as session:
        query = select(FeedbackModel)
        query = query.options(selectinload(FeedbackModel.upvoted_by))
        query = query.order_by(FeedbackModel.created_at.desc())

        return await paginate(
            conn=session,
            query=query,
            transformer=lambda x: [
                feedback.to_pydantic(current_user_id=user.id) for feedback in x
            ],
        )


async def fetch_feedback_model_by_id(feedback_id: UUID) -> Optional[FeedbackModel]:
    """Fetch feedback model by ID"""
    async with get_async_session() as session:
        statement = select(FeedbackModel).where(FeedbackModel.id == feedback_id)
        statement = statement.options(selectinload(FeedbackModel.upvoted_by))
        result = await session.execute(statement)
        return result.scalars().first()


async def count_feedback_for_user(user_id: UUID) -> int:
    """Count total feedback entries for a user"""
    async with get_async_session() as session:
        statement = select(func.count(FeedbackModel.id)).where(
            FeedbackModel.owner == user_id
        )
        result = await session.execute(statement)
        return result.scalar() or 0


async def toggle_feedback_upvote(
    feedback_id: UUID, user: User
) -> Optional[FeedbackUpvoteSchema]:
    """Toggle upvote for a feedback entry"""
    async with get_async_session() as session:
        # Check if feedback exists
        feedback_model = await fetch_feedback_model_by_id(feedback_id)
        if not feedback_model:
            logger.error(f"Feedback {feedback_id} not found")
            return None

        # Check if user already upvoted
        check_query = sql_select(feedback_upvote_association).where(
            feedback_upvote_association.c.feedback_id == feedback_id,
            feedback_upvote_association.c.user_id == user.id,
        )
        existing_upvote = await session.execute(check_query)
        has_upvoted = existing_upvote.first() is not None

        if has_upvoted:
            # Remove upvote
            delete_query = feedback_upvote_association.delete().where(
                feedback_upvote_association.c.feedback_id == feedback_id,
                feedback_upvote_association.c.user_id == user.id,
            )
            await session.execute(delete_query)
            logger.info(f"User {user.id} removed upvote from feedback {feedback_id}")
        else:
            # Add upvote
            insert_query = feedback_upvote_association.insert().values(
                feedback_id=feedback_id, user_id=user.id
            )
            await session.execute(insert_query)
            logger.info(f"User {user.id} upvoted feedback {feedback_id}")

        await session.commit()

        # Get updated feedback to return current state
        updated_feedback = await fetch_feedback_model_by_id(feedback_id)
        if updated_feedback:
            upvote_count = (
                len(updated_feedback.upvoted_by) if updated_feedback.upvoted_by else 0
            )
            return FeedbackUpvoteSchema(
                feedback_id=feedback_id,
                user_has_upvoted=not has_upvoted,  # Toggled state
                upvote_count=upvote_count,
            )

        return None


class FeedbackService:
    async def create_feedback(
        self, feedback_data: FeedbackCreateSchema, user: User
    ) -> Optional[FeedbackSchema]:
        return await create_feedback(feedback_data, user)

    async def get_feedback(
        self, feedback_id: UUID, user: User
    ) -> Optional[FeedbackSchema]:
        return await get_feedback(feedback_id, user)

    async def get_user_feedback(self, user: User) -> Page[FeedbackSchema]:
        return await get_user_feedback(user)

    async def update_feedback(
        self, feedback_id: UUID, feedback_data: FeedbackUpdateSchema, user: User
    ) -> Optional[FeedbackSchema]:
        return await update_feedback(feedback_id, feedback_data, user)

    async def get_all_feedback(self, user: User) -> Page[FeedbackSchema]:
        return await get_all_feedback(user)

    async def toggle_feedback_upvote(
        self, feedback_id: UUID, user: User
    ) -> Optional[FeedbackUpvoteSchema]:
        return await toggle_feedback_upvote(feedback_id, user)
