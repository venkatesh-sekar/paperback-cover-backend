from fastapi import APIRouter
from fastapi_users.router.oauth import get_oauth_router

from paperback_cover.auth.common import auth_backend, google_oauth_client
from paperback_cover.config import settings
from paperback_cover.registration.user_manager import get_user_manager

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


router.include_router(
    get_oauth_router(
        google_oauth_client,
        auth_backend,
        get_user_manager,
        settings.auth.secret,
        is_verified_by_default=True,
        redirect_url=f"{settings.ui.base_url}{settings.auth.oauth.google.callback_path}",
    ),
    prefix="/google",
)
