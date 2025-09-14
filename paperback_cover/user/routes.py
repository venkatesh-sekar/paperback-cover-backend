import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers

from paperback_cover.auth.common import auth_backend
from paperback_cover.auth.service import verify_active_user
from paperback_cover.models.user import User
from paperback_cover.registration.user_manager import get_user_manager
from paperback_cover.user.schema import UserSchema

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)


@router.get(
    "/me",
    response_model=UserSchema,
)
async def get_user(user: User = Depends(verify_active_user)) -> UserSchema:
    """Add credits to a specific user's account."""

    return UserSchema(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        credits=user.total_credits,
    )


current_user = fastapi_users.current_user()
