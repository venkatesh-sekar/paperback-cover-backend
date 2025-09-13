import enum

from pydantic import BaseModel


class AssetType(enum.Enum):
    IMAGE = "image"


class AssetSubType(enum.Enum):
    GENERIC = "generic"


class AssetSchema(BaseModel):
    id: str
    url: str
    type: AssetType
    sub_type: AssetSubType


class AssetUploadSchema(BaseModel):
    type: AssetType
    sub_type: AssetSubType
