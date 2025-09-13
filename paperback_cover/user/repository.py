from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from paperback_cover.commons.db import get_fastapi_users_async_session
from paperback_cover.models.auth import OAuthAccount
from paperback_cover.models.user import User


async def get_user_db(session: AsyncSession = Depends(get_fastapi_users_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)
