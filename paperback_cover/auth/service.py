from fastapi import Depends, HTTPException, Request, status

from paperback_cover.models.user import User
from paperback_cover.user.service import current_active_user


async def verify_active_user(
    request: Request, user: User = Depends(current_active_user)
):
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized action"
        )
    return user


async def verify_superuser(user: User = Depends(verify_active_user)):
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized action"
        )
    return user
