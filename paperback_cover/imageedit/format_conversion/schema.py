from enum import Enum

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Supported output formats"""

    JPEG = "JPEG"
    PNG = "PNG"
    PDF = "PDF"


class ConversionRequest(BaseModel):
    """Generic request schema for image format conversion"""

    output_format: OutputFormat
    dpi: int = Field(
        default=300, ge=72, le=600, description="DPI for output image/PDF (72-600)"
    )
    quality: int = Field(
        default=95,
        ge=1,
        le=100,
        description="JPEG quality (1-100, only for JPEG format)",
    )


class FormatConversionResponse(BaseModel):
    """Response schema for format conversion operations"""

    success: bool
    message: str
    file_url: str | None = None
    file_size_bytes: int | None = None
    format: str | None = None
    dpi: int | None = None
