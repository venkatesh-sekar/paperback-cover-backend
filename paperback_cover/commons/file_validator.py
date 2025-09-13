import logging
import os

from fastapi import HTTPException, UploadFile
from filetype import is_image

logger = logging.getLogger(__name__)


def get_file_extension(file_name: str) -> str:
    """Get the file extension from the file name."""
    return os.path.splitext(file_name)[1].lower()


async def validate_image_file(file: UploadFile):
    """Validate the uploaded file using libraries."""
    # Use the `filetype` library to validate the file type
    content = await file.read()
    await file.seek(0)  # Reset the file pointer
    if not is_image(content):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    # Limit file size (e.g., 10MB)
    max_file_size = 10 * 1024 * 1024  # 5MB
    if len(content) > max_file_size:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")
