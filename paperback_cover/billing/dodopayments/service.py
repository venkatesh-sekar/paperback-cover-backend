import logging
import uuid
from typing import Optional

from dodopayments import DodoPayments
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from paperback_cover.commons.db import get_async_session
from paperback_cover.config import settings
from paperback_cover.models.dodopayments import DodopaymentsUser
from paperback_cover.models.user import User

# Initialize DodoPayments client
dodopayments = DodoPayments(
    bearer_token=settings.billing.dodopayments.api_key,  # This should be set in environment variables
    environment=settings.billing.dodopayments.environment,  # Change to "live_mode" for production
)
logger = logging.getLogger(__name__)


async def get_user_from_customer_id(customer_id: str) -> Optional[User]:
    """Get user from Dodo Payments customer ID"""
    async with get_async_session() as session:
        result = await session.execute(
            select(DodopaymentsUser)
            .options(joinedload(DodopaymentsUser.user))
            .where(DodopaymentsUser.dodopayments_customer_id == customer_id)
        )
        dodopayments_user = result.unique().scalar_one_or_none()
        return dodopayments_user.user if dodopayments_user else None


async def sync_user_with_dodopayments(user_id: uuid.UUID) -> Optional[DodopaymentsUser]:
    """
    Syncs a specific user with DodoPayments using their ID.
    Creates a new customer in DodoPayments if one doesn't exist.
    """
    async with get_async_session() as session:
        try:
            # Fetch the user and relationship within the session
            result = await session.execute(
                select(User)
                .options(joinedload(User.dodopayments_user))
                .where(User.id == user_id)  # type: ignore
            )
            user = result.unique().scalar_one_or_none()

            if not user:
                logger.error(f"User with ID {user_id} not found for DodoPayments sync.")
                return None

            dodopayments_user = user.dodopayments_user
            dodopayments_customer_id = None

            # Create or update customer in DodoPayments
            customer_data = {
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
            }

            if dodopayments_user:
                dodopayments_customer_id = dodopayments_user.dodopayments_customer_id
                logger.info(
                    f"Updating DodoPayments Customer ID: {dodopayments_customer_id} for User {user.id}"
                )
                try:
                    # Update existing customer
                    updated_customer = dodopayments.customers.update(
                        dodopayments_customer_id, **customer_data
                    )
                    if updated_customer:
                        dodopayments_user.dodopayments_customer_id = (
                            updated_customer.customer_id
                        )
                except Exception as e:
                    logger.error(
                        f"Error updating DodoPayments customer {dodopayments_customer_id}: {e}",
                        exc_info=True,
                    )
                    raise
            else:
                # Create new customer
                logger.info(f"Creating DodoPayments Customer for User {user.id}")
                try:
                    new_customer = dodopayments.customers.create(**customer_data)
                    if new_customer:
                        dodopayments_customer_id = new_customer.customer_id
                        logger.info(
                            f"Created DodoPayments Customer ID: {dodopayments_customer_id}"
                        )

                        # Create new DodopaymentsUser record
                        dodopayments_user = DodopaymentsUser(
                            user_id=user.id,
                            dodopayments_customer_id=dodopayments_customer_id,
                        )
                        session.add(dodopayments_user)
                        await session.flush()
                        await session.refresh(dodopayments_user)
                        user.dodopayments_user = dodopayments_user
                except Exception as e:
                    logger.error(
                        f"Error creating DodoPayments customer for User {user.id}: {e}",
                        exc_info=True,
                    )
                    raise

            if not dodopayments_user or not dodopayments_customer_id:
                logger.error(
                    f"Failed to get/create DodoPayments user/customer ID for User {user.id}"
                )
                raise ValueError(
                    "Missing dodopayments_user or dodopayments_customer_id after customer sync."
                )

            # Commit Transaction
            await session.commit()
            await session.refresh(dodopayments_user)
            logger.info(
                f"Successfully synced User {user.id} with DodoPayments (Customer: {dodopayments_customer_id})"
            )
            return dodopayments_user

        except Exception as e:
            logger.error(
                f"Rolling back transaction for User {user_id} due to error: {e}",
                exc_info=True,
            )
            await session.rollback()
            return None


async def sync_all_users_with_dodopayments() -> None:
    """Syncs all users from the database with DodoPayments."""
    logger.info("Starting sync of all users with DodoPayments...")
    successful_syncs = 0
    failed_syncs = 0
    user_ids_to_sync = []

    # First, get all user IDs to avoid holding the session open for too long
    async with get_async_session() as session:
        try:
            result = await session.execute(select(User.id))  # type: ignore
            user_ids_to_sync = result.scalars().all()
            logger.info(f"Found {len(user_ids_to_sync)} user IDs to sync.")
        except Exception as e:
            logger.error(f"Failed to fetch user IDs for syncing: {e}", exc_info=True)
            return

    # Process each user sequentially to avoid overwhelming DodoPayments API rate limits
    for user_id in user_ids_to_sync:
        logger.info(f"Syncing User ID: {user_id}")
        synced_dodopayments_user = await sync_user_with_dodopayments(user_id)
        if synced_dodopayments_user:
            successful_syncs += 1
        else:
            failed_syncs += 1
            logger.error(f"Failed to sync User ID: {user_id}")

    logger.info(
        f"Finished syncing all users. Successful: {successful_syncs}, Failed: {failed_syncs}"
    )
