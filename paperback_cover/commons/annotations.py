import asyncio
import logging
from functools import wraps
from time import time

from paperback_cover.credit.service import reduce_user_credits

logger = logging.getLogger(__name__)


def timing(f):
    @wraps(f)
    async def wrap(*args, **kw):
        ts = time()
        if asyncio.iscoroutinefunction(f):
            result = await f(*args, **kw)
        else:
            result = f(*args, **kw)
        te = time()
        logger.info(f"func:{f.__name__} took: {te-ts:.4f} sec")
        return result

    return wrap


def reduce_credits(credit_amount: int):
    """
    A decorator that reduces a user's credits by a specified amount.
    The decorated function must receive a `user` keyword argument.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract the user; adjust this logic if the user is passed positionally.
            user = kwargs.get("user")
            if not user:
                raise ValueError("User parameter missing for credit reduction.")

            # Deduct the specified credits.
            new_balance = await reduce_user_credits(user, credit_amount)
            logger.info(
                f"Deducted {credit_amount} credits for {func.__name__}. New balance: {new_balance} | User: {user.id}"
            )

            # Continue with the execution of the original function.
            return await func(*args, **kwargs)

        return wrapper

    return decorator
