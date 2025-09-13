import os
import uuid
from typing import AsyncGenerator, List, Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)
from httpx_oauth.clients.google import GoogleOAuth2
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

from paperback_cover.commons.db import (
    get_async_session,
    get_fastapi_users_async_session,
)
from paperback_cover.config import settings
from paperback_cover.models.auth import OAuthAccount
from paperback_cover.models.base import DATABASE_URL, Base
from paperback_cover.models.user import User


async def get_user_db(session: AsyncSession = Depends(get_fastapi_users_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)
