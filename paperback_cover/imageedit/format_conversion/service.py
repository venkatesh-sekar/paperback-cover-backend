import logging
from io import BytesIO
from typing import Optional, Tuple

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from paperback_cover.imageedit.format_conversion.schema import (
    ConversionRequest,
    OutputFormat,
)
from paperback_cover.models.user import User

logger = logging.getLogger(__name__)


class ImageFormatConversionService:
    """Service for converting images to different formats and specifications"""

    def __init__(self):
        pass

    async def convert_image(
        self,
        file: UploadFile,
        conversion_request: ConversionRequest,
        user: User,
    ) -> Optional[Tuple[BytesIO, str, str]]:
        """
        Convert an image to the specified format with given parameters.

        Args:
            file: The uploaded image file
            conversion_request: Conversion parameters (format, DPI, quality, etc.)
            user: The authenticated user

        Returns:
            A tuple containing the file buffer, filename, and media type, or None on failure.
        """

        # Read the uploaded file
        file_content = await file.read()
        try:
            image = Image.open(BytesIO(file_content))
        except UnidentifiedImageError:
            return None

        original_filename = file.filename or "image"
        filename_no_ext, _ = original_filename.rsplit(".", 1)

        # Convert based on output format
        if conversion_request.output_format == OutputFormat.PDF:
            buffer, extension = await self._convert_to_pdf(image, conversion_request)
            media_type = "application/pdf"
        else:
            buffer, extension = await self._convert_to_image(image, conversion_request)
            media_type = (
                "image/jpeg"
                if conversion_request.output_format == OutputFormat.JPEG
                else "image/png"
            )

        new_filename = f"{filename_no_ext}{extension}"

        return buffer, new_filename, media_type

    async def _convert_to_image(
        self,
        image: Image.Image,
        conversion_request: ConversionRequest,
    ) -> Tuple[BytesIO, str]:
        """Convert image to JPEG or PNG format"""

        # Convert to appropriate mode for output format
        if (
            conversion_request.output_format == OutputFormat.JPEG
            and image.mode != "RGB"
        ):
            image = image.convert("RGB")
        elif (
            conversion_request.output_format == OutputFormat.PNG
            and image.mode not in ["RGB", "RGBA"]
        ):
            image = image.convert("RGBA")

        # Save the image with specified parameters
        output_buffer = BytesIO()
        save_kwargs = {
            "format": conversion_request.output_format.value,
            "dpi": (conversion_request.dpi, conversion_request.dpi),
            "optimize": True,
        }

        # Add quality parameter only for JPEG
        if conversion_request.output_format == OutputFormat.JPEG:
            save_kwargs["quality"] = conversion_request.quality

        image.save(output_buffer, **save_kwargs)
        output_buffer.seek(0)

        file_extension = (
            ".jpg" if conversion_request.output_format == OutputFormat.JPEG else ".png"
        )

        return output_buffer, file_extension

    async def _convert_to_pdf(
        self,
        image: Image.Image,
        conversion_request: ConversionRequest,
    ) -> Tuple[BytesIO, str]:
        """Convert image to PDF format"""

        # Convert to RGB if necessary
        if image.mode not in ["RGB", "RGBA"]:
            image = image.convert("RGB")

        # Get image dimensions
        img_width, img_height = image.size

        # Create PDF buffer
        pdf_buffer = BytesIO()

        # Create PDF with exact image dimensions (in points)
        # Convert pixels to points (1 inch = 72 points)
        pdf_width = (img_width / conversion_request.dpi) * 72
        pdf_height = (img_height / conversion_request.dpi) * 72

        # Create canvas with custom page size
        c = canvas.Canvas(pdf_buffer, pagesize=(pdf_width, pdf_height))

        # Draw image on PDF (full page, no margins)
        c.drawImage(
            ImageReader(image),
            0,
            0,
            width=pdf_width,
            height=pdf_height,
            preserveAspectRatio=True,
            mask="auto",
        )

        c.save()
        pdf_buffer.seek(0)

        return pdf_buffer, ".pdf"


def get_image_format_conversion_service() -> ImageFormatConversionService:
    return ImageFormatConversionService()
