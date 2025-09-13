import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi_pagination import Page

from paperback_cover.auth.service import verify_active_user
from paperback_cover.models.user import User
from paperback_cover.userassets.schema import AssetSchema, AssetType, AssetUploadSchema
from paperback_cover.userassets.service import fetch_assets, upload_asset

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assets",
    tags=["assets", "user"],
)


@router.get("")
async def fetch_all_assets_api(
    user: User = Depends(verify_active_user),
) -> Page[AssetSchema]:
    return await fetch_assets(user)


@router.get("/images")
async def fetch_all_images_api(
    user: User = Depends(verify_active_user),
) -> Page[AssetSchema]:
    return await fetch_assets(user, AssetType.IMAGE)


@router.post("")
async def upload_user_asset(
    data: str = Form(...),
    asset: UploadFile = File(...),
    user: User = Depends(verify_active_user),
) -> AssetSchema:
    upload_schema = AssetUploadSchema.model_validate_json(json_data=data)
    return await upload_asset(upload_schema, asset, user)
