import logging
from uuid import UUID

from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from paperback_cover.auth.common import auth_backend
from paperback_cover.models.user import User
from paperback_cover.registration.user_manager import get_user_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()
