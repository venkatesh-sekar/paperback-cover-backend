from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page

from paperback_cover.auth.service import verify_active_user
from paperback_cover.commons.annotations import timing
from paperback_cover.feedback.schema import (
    FeedbackCreateSchema,
    FeedbackSchema,
    FeedbackUpdateSchema,
    FeedbackUpvoteSchema,
)
from paperback_cover.feedback.service import (
    create_feedback,
    get_all_feedback,
    get_feedback,
    get_user_feedback,
    toggle_feedback_upvote,
    update_feedback,
)
from paperback_cover.models.user import User

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
)


@router.post("")
@timing
async def create_feedback_router(
    feedback_data: FeedbackCreateSchema, user: User = Depends(verify_active_user)
) -> FeedbackSchema:
    """Create a new feedback entry"""
    created_feedback = await create_feedback(feedback_data, user)
    if not created_feedback:
        raise HTTPException(status_code=400, detail="Feedback could not be created")
    return created_feedback


@router.get("/my-feedback")
@timing
async def get_my_feedback_router(
    user: User = Depends(verify_active_user),
) -> Page[FeedbackSchema]:
    """Get all feedback entries for the current user"""
    return await get_user_feedback(user)


@router.get("")
@timing
async def get_all_feedback_router(
    user: User = Depends(verify_active_user),
) -> Page[FeedbackSchema]:
    return await get_all_feedback(user)


@router.get("/{feedback_id}")
@timing
async def get_feedback_router(
    feedback_id: UUID, user: User = Depends(verify_active_user)
) -> FeedbackSchema:
    """Get a specific feedback entry"""
    feedback = await get_feedback(feedback_id, user)
    if not feedback:
        raise HTTPException(
            status_code=404, detail="Feedback not found or access denied"
        )
    return feedback


@router.put("/{feedback_id}")
@timing
async def update_feedback_router(
    feedback_id: UUID,
    feedback_data: FeedbackUpdateSchema,
    user: User = Depends(verify_active_user),
) -> FeedbackSchema:
    """Update a feedback entry"""
    updated_feedback = await update_feedback(feedback_id, feedback_data, user)
    if not updated_feedback:
        raise HTTPException(
            status_code=400, detail="Feedback could not be updated or not found"
        )
    return updated_feedback


@router.post("/{feedback_id}/upvote")
@timing
async def toggle_feedback_upvote_router(
    feedback_id: UUID, user: User = Depends(verify_active_user)
) -> FeedbackUpvoteSchema:
    """Toggle upvote for a feedback entry"""
    upvote_result = await toggle_feedback_upvote(feedback_id, user)
    if not upvote_result:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return upvote_result
