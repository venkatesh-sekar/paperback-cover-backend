from pydantic import BaseModel


class UploadMetadata(BaseModel):
    artwork_type: str
    user_id: str
    artwork_status: str
    artwork_width: str
    artwork_height: str


class ImageUploadMetadata(BaseModel):
    image_width: str
    image_height: str
