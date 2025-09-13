import json
import logging
import uuid
from typing import Optional

from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import select

from paperback_cover.auth.common import google_oauth_client
from paperback_cover.billing.dodopayments.service import sync_user_with_dodopayments
from paperback_cover.commons.db import get_async_session
from paperback_cover.config import settings
from paperback_cover.models.auth import OAuthAccount
from paperback_cover.models.user import User
from paperback_cover.user.repository import get_user_db

logger = logging.getLogger(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.auth.secret
    verification_token_secret = settings.auth.secret

    async def update_name(self, user: User | None = None):
        if not user:
            return
        async with get_async_session() as session:
            result = await session.execute(select(OAuthAccount).where(OAuthAccount.user_id == user.id))  # type: ignore
            oauth_account: OAuthAccount | None = result.scalar_one_or_none()
            if oauth_account:
                token = oauth_account.access_token
                name_details = None
                if oauth_account.oauth_name == "google":
                    name_details = (
                        await google_oauth_client.get_user_first_and_last_name(token)
                    )

                if name_details:
                    user.first_name = name_details.first_name
                    user.last_name = name_details.last_name
                    await self.user_db.update(
                        user,
                        {"first_name": user.first_name, "last_name": user.last_name},
                    )
                    logger.info(f"Successfully updated name for user {user.id}")
                else:
                    logger.error(f"Failed to update name for user {user.id}")
            else:
                logger.error(f"No OAuth account found for user {user.id}")

    async def on_after_register(self, user: User, request: Optional[Request] = None):

        logger.info(f"User {user.id} has registered with email {user.email}")
        try:
            await self.update_name(user)
            logger.info(f"Successfully created UserData for new user {user.id}")

            # Sync with DodoPayments
            try:
                await sync_user_with_dodopayments(user.id)
                logger.info(f"Successfully synced user {user.id} with DodoPayments")
            except Exception as e:
                logger.error(
                    f"Failed to sync user {user.id} with DodoPayments: {e}",
                    exc_info=True,
                )
        except Exception as e:
            logger.error(
                f"Failed to create UserData for new user {user.id}: {e}", exc_info=True
            )

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        if response:
            access_token = json.loads(response.body)["access_token"]
            response.set_cookie("token", access_token)
            # redirect to the home page
            response.headers["Location"] = "/"
            response.status_code = 302


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)
