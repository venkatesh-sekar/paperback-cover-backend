from fastapi import Depends
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.authentication.strategy.db import (
    AccessTokenDatabase,
    DatabaseStrategy,
)

from paperback_cover.auth.oauth_providers.google import GoogleOauth2Provider
from paperback_cover.auth.repository import get_access_token_db
from paperback_cover.config import settings
from paperback_cover.models.auth import AccessToken

bearer_transport = BearerTransport(tokenUrl="auth/email/login")


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db, lifetime_seconds=settings.auth.expiration)


auth_backend = AuthenticationBackend(
    name="auth_backend",
    transport=bearer_transport,
    get_strategy=get_database_strategy,
)

google_oauth_client = GoogleOauth2Provider(
    settings.auth.oauth.google.client_id,
    settings.auth.oauth.google.client_secret,
)
