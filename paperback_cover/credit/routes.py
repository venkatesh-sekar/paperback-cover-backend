import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from paperback_cover.auth.service import verify_superuser
from paperback_cover.credit.schema import CreditAddSchema
from paperback_cover.credit.service import add_credits, expire_credits_task
from paperback_cover.user.schema import UserDataSchema
from paperback_cover.user.service import get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/credits",
    tags=["credits"],
)


@router.post(
    "/users/{user_id}",
    response_model=UserDataSchema,
    dependencies=[Depends(verify_superuser)],
)
async def add_user_credits(
    user_id: UUID,
    credit_data: CreditAddSchema,
) -> UserDataSchema:
    """Add credits to a specific user's account."""
    target_user = await get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = await add_credits(target_user, credit_data)
    return user_data


@router.post(
    "/expire",
    tags=["admin"],
    dependencies=[Depends(verify_superuser)],
    status_code=200,
)
async def expire_credits():
    """Expires credits that have passed their expiration date."""
    try:
        await expire_credits_task()
        return {"message": "Credits expired successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during credit expiration: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred during credit expiration.",
        )
