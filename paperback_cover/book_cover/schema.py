from pydantic import BaseModel


class BoundingBoxSchema(BaseModel):
    x: int
    y: int
    width: int
    height: int
