import logging
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from filetype import guess_extension
from sqlalchemy import func, select

from paperback_cover.commons.db import get_async_session
from paperback_cover.commons.file_validator import validate_image_file
from paperback_cover.models.asset import UserAsset
from paperback_cover.models.user import User
from paperback_cover.storage_service.service import (
    delete_blob_from_bucket,
    get_user_generated_url_for_object,
    upload_blob_to_bucket,
)
from paperback_cover.userassets.schema import AssetSchema, AssetType, AssetUploadSchema

logger = logging.getLogger(__name__)


def map_model_to_schema(asset: UserAsset) -> AssetSchema:

    return AssetSchema(
        id=str(asset.id),
        name=asset.name,
        url=(get_user_generated_url_for_object(asset.path)) or "",
        type=AssetType(asset.type),
    )


async def fetch_assets(
    user: User, asset_type: Optional[AssetType] = None
) -> Page[AssetSchema]:
    async with get_async_session() as session:
        return await paginate(
            conn=session,
            query=select(UserAsset)
            .filter_by(owner=user.id, type=asset_type.value if asset_type else None)
            .order_by(UserAsset.created_at),
            transformer=lambda x: [map_model_to_schema(i) for i in x],
        )


async def check_user_asset_count(user: User, asset_type: AssetType, limit: int = 10):
    """
    Checks if the user has reached the asset limit for the given type.
    Raises HTTPException if limit exceeded.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count(UserAsset.id)).where(
                UserAsset.owner == user.id, UserAsset.type == asset_type.value
            )
        )
        count = result.scalar()
    if count is None:
        count = 999999999
    if count >= limit:
        raise HTTPException(
            status_code=400,
            detail=f"You have reached the maximum of {limit} {asset_type.name.lower()} assets allowed.",
        )


async def upload_asset(
    uploadSchema: AssetUploadSchema, asset: UploadFile, user: User
) -> AssetSchema:
    await check_user_asset_count(user, uploadSchema.type, 20)

    # Validate the file
    await validate_image_file(asset)

    # Get file extension
    file_extension = guess_extension(asset.file)
    if not file_extension or file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=400, detail="Only JPG, JPEG, and PNG files are allowed."
        )

    asset_id = str(uuid.uuid4())
    object_name = f"users/{str(user.id)}/assets/{uploadSchema.type.value}/{uploadSchema.sub_type.name}/{asset_id}.{file_extension}"

    async with get_async_session() as session:
        async with session.begin():
            try:
                logger.info(f"Uploading asset to bucket: {object_name}")
                await upload_blob_to_bucket(
                    await asset.read(),  # Read file content
                    path=object_name,
                    metadata=uploadSchema.model_dump(mode="json"),
                )

                session.add(
                    UserAsset(
                        id=asset_id,
                        path=object_name,
                        type=uploadSchema.type.value,
                        sub_type=uploadSchema.sub_type.value,
                        owner=user.id,
                    )
                )
                await session.commit()

            except Exception as e:
                logger.error(f"Error in asset upload: {e}", exc_info=True)
                await session.rollback()
                await delete_blob_from_bucket(object_name)
                raise HTTPException(status_code=500, detail="Asset upload failed.")
            else:
                logger.info("Database transaction committed.")

    result = await fetch_asset_by_id(asset_id)
    if not result:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve the inserted object."
        )
    return map_model_to_schema(result)


async def fetch_asset_by_id(id: str) -> UserAsset | None:
    async with get_async_session() as session:
        result = await session.execute(select(UserAsset).filter_by(id=id))
        return result.scalar_one_or_none()


async def delete_asset_by_id(id: str, user: User):
    async with get_async_session() as session:
        async with session.begin():
            asset = await fetch_asset_by_id(id)
            if not asset:
                raise HTTPException(status_code=404, detail="Asset not found.")

            if asset.owner != user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You are not authorized to delete this asset.",
                )

            try:
                logger.info(f"Deleting asset from bucket: {asset.path}")
                await delete_blob_from_bucket(asset.path)

                await session.delete(asset)
                await session.commit()
            except Exception as e:
                logger.error(f"Error in asset deletion: {e}", exc_info=True)
                await session.rollback()
                raise HTTPException(status_code=500, detail="Asset deletion failed.")
            else:
                logger.info("Database transaction committed.")


# Added function to return the count of assets for a given user and asset type
async def get_user_asset_count(user: User, asset_type: AssetType) -> int:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count(UserAsset.id)).where(
                UserAsset.owner == user.id, UserAsset.type == asset_type.value
            )
        )
        return result.scalar() or 0
