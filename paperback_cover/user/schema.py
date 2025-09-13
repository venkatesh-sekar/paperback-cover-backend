from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from paperback_cover.credit.schema import CreditSchema


class UserDataSchema(BaseModel):
    user_id: UUID
    credits: List[CreditSchema] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)

    class Config:
        from_attributes = True
        populate_by_name = True


class UserUpdateResponseSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str

    class Config:
        from_attributes = True
        populate_by_name = True
