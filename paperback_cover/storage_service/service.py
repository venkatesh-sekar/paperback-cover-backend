import enum
import logging
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from cloudflare import Cloudflare

from paperback_cover.commons.annotations import timing
from paperback_cover.config import settings
from paperback_cover.storage_service.schema import UploadMetadata

logger = logging.getLogger(__name__)


class S3ContentType(enum.Enum):
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_GIF = "image/gif"
    IMAGE_WEBP = "image/webp"
    APPLICATION_PDF = "application/pdf"
    APPLICATION_ZIP = "application/zip"
    APPLICATION_X_TAR = "application/x-tar"


class S3Uploader:
    def __init__(self, bucket_name, access_key, secret_key, region_name, endpoint):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            endpoint_url=endpoint,
            config=Config(signature_version="s3v4"),
        )

    async def upload_image_multipart(self, image_data, object_name, metadata):
        """
        Uploads an image in parts to an S3 bucket using multipart upload.

        Parameters:
            image_data (bytes): The binary data of the image.
            object_name (str): The S3 object name under which the image will be stored.
            metadata (dict): A dictionary containing the metadata for the image.
        """
        # Create a multipart upload
        multipart = self.s3_client.create_multipart_upload(
            Bucket=self.bucket_name, Key=object_name, Metadata=metadata
        )
        upload_id = multipart["UploadId"]
        try:

            # Split the file into chunks
            part_size = 5 * 1024 * 1024  # 5 MB per part
            parts = [
                image_data[i : i + part_size]
                for i in range(0, len(image_data), part_size)
            ]

            part_info = {"Parts": []}

            # Upload parts
            for part_number, part in enumerate(parts, start=1):
                response = self.s3_client.upload_part(
                    Body=part,
                    Bucket=self.bucket_name,
                    Key=object_name,
                    PartNumber=part_number,
                    UploadId=upload_id,
                )
                part_info["Parts"].append(
                    {"PartNumber": part_number, "ETag": response["ETag"]}
                )

            # Complete multipart upload
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=object_name,
                UploadId=upload_id,
                MultipartUpload=part_info,
            )
            logger.info(f"Image uploaded successfully: {object_name}")

            return get_user_generated_url_for_object(object_name)
        except NoCredentialsError:
            logger.error("Credentials are not available.")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}, aborting upload.")

            # Aborting upload in case of exception
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name, Key=object_name, UploadId=upload_id
            )

    async def upload_object(self, data, object_name, metadata):
        """
        Uploads an object to an S3 bucket.

        Parameters:
            data (bytes): The binary data to be uploaded.
            object_name (str): The name of the object under which the data will be stored.
            metadata (dict): A dictionary containing the metadata for the data.
        """
        try:
            response = self.s3_client.put_object(
                Bucket=self.bucket_name, Key=object_name, Body=data, Metadata=metadata
            )
            logger.info(f"Object uploaded successfully: {object_name}")
            return object_name
        except NoCredentialsError:
            logger.error("Credentials are not available.")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")

    async def delete_object(self, object_name):
        """
        Deletes an object from an S3 bucket.

        Parameters:
            object_name (str): The name of the object to be deleted.
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"Object deleted successfully: {object_name}")
        except NoCredentialsError:
            logger.error("Credentials are not available.")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")

    async def move_object(self, object_name, new_object_name):
        """
        Moves an object from one location to another within the same bucket.

        Parameters:
            object_name (str): The name of the object to be moved.
            new_object_name (str): The new name of the object.
        """
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": object_name}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=new_object_name,
            )
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(
                f"Object moved successfully: {object_name} -> {new_object_name}"
            )
        except NoCredentialsError:
            logger.error("Credentials are not available.")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")


uploader = S3Uploader(
    bucket_name=settings.storage.user_generated.bucket,
    access_key=settings.storage.user_generated.access_key,
    secret_key=settings.storage.user_generated.secret_key,
    region_name=settings.storage.user_generated.region,
    endpoint=settings.storage.user_generated.endpoint,
)


client = Cloudflare(
    api_token=settings.storage.cloudflare_images.token,
)


@timing
async def upload_image_to_bucket(
    image_data: bytes, image_name: str, metadata: UploadMetadata
) -> str | None:
    """
    Uploads an image to an S3 bucket.

    Parameters:
        image_data (bytes): The binary data of the image.
        object_name (str): The S3 object name under which the image will be stored.
        metadata (UploadMetadata): The metadata for the image.
    """
    return await uploader.upload_image_multipart(
        image_data, image_name, metadata.model_dump(mode="json")
    )


def get_user_generated_url_for_object(object_name: str) -> str:
    """
    Returns the URL of an object stored in the user-generated bucket.

    Parameters:
        object_name (str): The name of the object.
    """
    return f"{settings.storage.user_generated.public_url}/{object_name}"


@timing
async def upload_blob_to_bucket(
    blob_data: bytes, path: str, metadata: dict
) -> str | None:
    """
    Uploads a blob to an S3 bucket.

    Parameters:
        blob_data (bytes): The binary data of the blob.
        blob_name (str): The S3 object name under which the blob will be stored.
        metadata (UploadMetadata): The metadata for the blob.
    """
    logger.info(f"Uploading blob to bucket: {path}")
    return await uploader.upload_object(blob_data, path, metadata)


@timing
async def upload_temp_file_to_bucket(blob_data: bytes, suffix: str = "") -> str | None:
    temp_path = "temp/" + str(uuid.uuid4()) + suffix
    return await upload_blob_to_bucket(blob_data, temp_path, {})
