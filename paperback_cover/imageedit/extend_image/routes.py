import logging

from fastapi import APIRouter, Depends

from paperback_cover.auth.service import verify_active_user
from paperback_cover.commons.annotations import reduce_credits, timing
from paperback_cover.imageedit.extend_image.schema import ExtendImageRequest
from paperback_cover.imageedit.extend_image.service import (
    ExtendImageService,
    get_extend_image_service,
)
from paperback_cover.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/imageedit/extend",
    tags=["imageedit,extend"],
)


@router.post("")
@timing
@reduce_credits(6)
async def extend_image_api(
    extend_image_request: ExtendImageRequest,
    user: User = Depends(verify_active_user),
    extend_image_service: ExtendImageService = Depends(get_extend_image_service),
):
    return await extend_image_service.extend_image(
        extend_image_request,
        user,
    )
