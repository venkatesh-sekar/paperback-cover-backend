import logging
import uuid
from typing import Optional

from fastapi_users import FastAPIUsers

from paperback_cover.auth.common import auth_backend
from paperback_cover.commons.db import get_async_session
from paperback_cover.models.user import User
from paperback_cover.registration.user_manager import get_user_manager
from paperback_cover.user.schema import UserUpdateResponseSchema, UserUpdateSchema

logger = logging.getLogger(__name__)

fastapi_users_service = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users_service.current_user(optional=True)


async def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    async with get_async_session() as session:
        result = await session.get(User, user_id)
        return result


async def update_user_details(
    user: User, user_update: UserUpdateSchema
) -> UserUpdateResponseSchema:
    """Update user's first name and last name."""
    logger.info(f"Updating user details for user {user.id}")
    async with get_async_session() as session:
        if user_update.first_name is not None:
            user.first_name = user_update.first_name
        if user_update.last_name is not None:
            user.last_name = user_update.last_name

        session.add(user)
        await session.commit()

        return UserUpdateResponseSchema(
            first_name=user.first_name, last_name=user.last_name, email=user.email
        )
