import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile

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
@reduce_credits(1)
async def extend_image_api(
    data: str = Form(..., description="JSON string containing extension parameters"),
    file: UploadFile = File(...),
    user: User = Depends(verify_active_user),
    extend_image_service: ExtendImageService = Depends(get_extend_image_service),
):
    """
    Extend an image to target dimensions using AI inpainting.

    - **data**: JSON string containing extension parameters:
        - target_width: Target width in pixels
        - target_height: Target height in pixels
        - original_box: Bounding box of original image within target canvas
        - invert_text: Whether to invert mask for text processing (default: true)
        - remove_text: Whether to remove text before extending (default: false)
    - **file**: The image file to extend
    """
    extend_image_request = ExtendImageRequest.parse_raw(data)
    return await extend_image_service.extend_image(
        extend_image_request,
        file,
        user,
    )
