import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from paperback_cover.auth.service import verify_active_user
from paperback_cover.commons.annotations import timing
from paperback_cover.imageedit.format_conversion.schema import ConversionRequest
from paperback_cover.imageedit.format_conversion.service import (
    ImageFormatConversionService,
    get_image_format_conversion_service,
)
from paperback_cover.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/imageedit/format_conversion",
    tags=["imageedit", "format_conversion"],
)


@router.post("/convert")
@timing
async def convert_image_format_api(
    data: str = Form(..., description="JSON string containing conversion parameters"),
    file: UploadFile = File(...),
    user: User = Depends(verify_active_user),
    format_conversion_service: ImageFormatConversionService = Depends(
        get_image_format_conversion_service
    ),
) -> StreamingResponse:
    """
    Convert an image file to the specified format with custom parameters.

    - **data**: JSON string containing conversion parameters:
        - book_id: The ID of the book this image belongs to
        - output_format: Target format (JPEG, PNG, PDF)
        - dpi: DPI for output (72-600, default: 300)
        - quality: JPEG quality 1-100 (default: 95, only for JPEG)
    - **file**: The image file to convert

    Examples:
    - For ebook: {"book_id": "123", "output_format": "JPEG", "dpi": 300, "quality": 95}
    - For print: {"book_id": "123", "output_format": "PDF", "dpi": 300, "quality": 100}
    - For web: {"book_id": "123", "output_format": "PNG", "dpi": 72}
    """
    conversion_request = ConversionRequest.parse_raw(data)
    result = await format_conversion_service.convert_image(
        file=file,
        conversion_request=conversion_request,
        user=user,
    )
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to convert image. Please check the file and parameters.",
        )

    file_buffer, filename, media_type = result
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        content=file_buffer, media_type=media_type, headers=headers
    )
