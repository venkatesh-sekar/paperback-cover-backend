import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select

from paperback_cover.commons.db import get_async_session
from paperback_cover.credit.schema import CreditAddSchema
from paperback_cover.models.credit import Credit, CreditStatus
from paperback_cover.models.user import User

logger = logging.getLogger(__name__)

BATCH_SIZE = 500  # Define batch size for processing


def _create_credit_object(
    user_data_id: UUID,
    amount: int,
    expires_at: Optional[datetime],
    is_from_plan: bool,
) -> Credit:
    """Helper function to create a Credit object without session interaction."""
    if amount <= 0:
        raise ValueError("Credit amount must be positive")

    naive_expires_at = expires_at
    if expires_at and expires_at.tzinfo is not None:
        logger.debug(f"Converting aware datetime {expires_at} to naive UTC")
        naive_expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
    elif expires_at:
        logger.debug(f"Using naive datetime {expires_at} as is")

    return Credit(
        user_data_id=user_data_id,
        amount=amount,
        expires_at=naive_expires_at,
        is_from_plan=is_from_plan,
        status=CreditStatus.ACTIVE,
    )


async def add_credits(user: User, credit_data: CreditAddSchema) -> Credit:
    """Add credits to a user's account."""
    async with get_async_session() as session:
        async with session.begin():
            credit = _create_credit_object(
                user_data_id=user.id,
                amount=credit_data.amount,
                expires_at=credit_data.expires_at,
                is_from_plan=credit_data.is_from_plan,
            )
            session.add(credit)
            return credit


async def reduce_user_credits(user: User, credits_to_reduce: int) -> int:
    """Reduce a user's credits by the specified amount."""

    logger.info(f"Reducing credits for user {user.id} by {credits_to_reduce}")

    if credits_to_reduce <= 0:
        raise ValueError("Credits to reduce must be positive")

    async with get_async_session() as session:
        async with session.begin():
            now = datetime.now(timezone.utc)

            # Get active credits ordered by expiration date (null last)
            result = await session.execute(
                select(Credit)
                .where(
                    Credit.user_id == user.id,
                    Credit.status == CreditStatus.ACTIVE,
                    or_(
                        Credit.expires_at.is_(None),
                        Credit.expires_at > now.replace(tzinfo=None),
                    ),
                )
                .order_by(
                    Credit.expires_at.is_(None),  # Nulls last
                    Credit.expires_at,  # Then by expiration date
                )
            )
            active_credits = result.scalars().all()

            remaining_to_reduce = credits_to_reduce
            credits_reduced = 0

            current_total_credits = sum(credit.amount for credit in active_credits)

            for credit in active_credits:
                if remaining_to_reduce <= 0:
                    break

                if credit.amount <= remaining_to_reduce:
                    # Use all of this credit
                    remaining_to_reduce -= credit.amount
                    credits_reduced += credit.amount
                    credit.status = CreditStatus.CONSUMED
                else:
                    # Only use part of this credit
                    credit.amount -= remaining_to_reduce
                    credits_reduced += remaining_to_reduce
                    remaining_to_reduce = 0

            new_total_credits = -1
            if remaining_to_reduce > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient credits. Required: {credits_to_reduce}, Available: {credits_reduced}",
                )
            else:
                await session.commit()
                new_total_credits = sum(credit.amount for credit in active_credits)
                logger.info(
                    f"Credits reduced for user {user.id} by {credits_reduced} | Current total credits: {current_total_credits} | New total credits: {new_total_credits}"
                )

            return new_total_credits


async def get_remaining_credit(user: User) -> int:
    """Get the total remaining credits for a user."""
    return user.total_credits if user else 0


async def expire_credits_task():
    """Expire credits that have passed their expiration date."""
    async with get_async_session() as session:
        async with session.begin():
            current_time = datetime.now(timezone.utc)
            # Find credits that should be expired
            result = await session.execute(
                select(Credit).where(
                    Credit.status == CreditStatus.ACTIVE,
                    Credit.expires_at.isnot(None),
                    Credit.expires_at < current_time,
                )
            )
            expired_credits = result.scalars().all()

            # Update status to expired
            for credit in expired_credits:
                credit.status = CreditStatus.EXPIRED

            logger.info(f"Expired {len(expired_credits)} credits")
