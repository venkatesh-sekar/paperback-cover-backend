from pydantic import BaseModel

from paperback_cover.book_cover.schema import BoundingBoxSchema


class ExtendImageRequest(BaseModel):
    image_url: str
    target_width: int
    target_height: int
    original_box: BoundingBoxSchema
    invert_text: bool = True
    remove_text: bool = False
