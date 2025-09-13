from fastapi import Depends
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from paperback_cover.commons.db import get_fastapi_users_async_session
from paperback_cover.models.auth import AccessToken


async def get_access_token_db(
    session: AsyncSession = Depends(get_fastapi_users_async_session),
):
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
