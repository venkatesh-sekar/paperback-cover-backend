import datetime
import logging
import uuid
from io import BytesIO

import httpx
from fastapi import Depends, UploadFile
from PIL import Image, ImageDraw

from paperback_cover.commons.db import get_async_session
from paperback_cover.commons.file_validator import validate_image_file
from paperback_cover.cover_art.replicate_artwork_service import (
    ReplicateArtworkService,
    get_replicate_artwork_service,
)
from paperback_cover.cover_art.schema import CoverArtSchema, OcrResult
from paperback_cover.imageedit.extend_image.schema import ExtendImageRequest
from paperback_cover.models.asset import UserAsset
from paperback_cover.models.user import User
from paperback_cover.openai.background_analyser_service import (
    BackgroundAnalyserService,
    get_background_analyser_service,
)
from paperback_cover.storage_service.schema import UploadMetadata
from paperback_cover.storage_service.service import (
    get_user_generated_url_for_object,
    upload_image_to_bucket,
    upload_temp_file_to_bucket,
)

logger = logging.getLogger(__name__)


def map_model_to_schema(cover_artwork: UserAsset) -> CoverArtSchema:
    return CoverArtSchema(
        id=str(cover_artwork.id),
        image_url=get_user_generated_url_for_object(cover_artwork.path),
        created_at=cover_artwork.created_at,
    )


async def add_extended_image(
    image_url: str,
    user: User,
) -> CoverArtSchema | None:
    """
    Add the extended image to the database.
    """
    try:
        async with get_async_session() as session:
            async with session.begin():
                model = UserAsset(
                    artwork_url=image_url,
                    owner=user.id,
                    path=image_url,
                    type="paperback_cover",
                )
                session.add(model)
                await session.commit()
                return map_model_to_schema(model)
    except Exception as e:
        logger.error(f"Error adding extended image: {e}")
        return None


class ExtendImageService:
    def __init__(
        self,
        replicate_artwork_service: ReplicateArtworkService,
        background_analyser_service: BackgroundAnalyserService,
    ):
        self.replicate_artwork_service = replicate_artwork_service
        self.background_analyser_service = background_analyser_service

    async def extend_image(
        self, request: ExtendImageRequest, file: UploadFile, user: User
    ) -> CoverArtSchema | None:
        logger.info(f"Starting image extension request: {request.model_dump()}")

        # First, upload the input image to get a URL for background analysis
        try:
            await validate_image_file(file)
            file_content = await file.read()
            original_image = Image.open(BytesIO(file_content)).convert("RGBA")

            # Upload the original image to get a URL for background analysis
            uploaded_image = await self._upload_image_to_storage(original_image)
            image_url_for_analysis = uploaded_image.image_url
        except Exception as e:
            logger.error(f"Failed to process uploaded image: {e}")
            raise Exception("Failed to process uploaded image") from e

        background_prompt = await self.background_analyser_service.anlayse_background(
            image_url_for_analysis
        )

        if background_prompt is None:
            logger.error("Failed to analyse background")
            return None

        # --- Text handling ---
        original_image_with_text = original_image.copy()
        saved_text_patches = []
        if request.remove_text:
            try:
                ocr_result: OcrResult = (
                    await self.replicate_artwork_service.detect_text_with_region(
                        image_url=image_url_for_analysis
                    )
                )
                logger.info(f"Detected {len(ocr_result.regions)} text regions.")
            except Exception as e:
                logger.error(f"Failed to detect text regions: {e}", exc_info=True)
                ocr_result = OcrResult(regions=[])

            if ocr_result.regions:
                # First, save all the text patches that need to be restored later.
                for region in ocr_result.regions:
                    poly_bbox = self._get_bounding_box_for_polygon(region.bounding_box)
                    mask = Image.new("L", original_image.size, 0)
                    ImageDraw.Draw(mask).polygon(region.bounding_box, fill=255)
                    cropped_mask = mask.crop(poly_bbox)
                    patch = original_image_with_text.crop(poly_bbox)
                    final_patch = Image.new("RGBA", patch.size, (0, 0, 0, 0))
                    final_patch.paste(patch, (0, 0), cropped_mask)
                    saved_text_patches.append({"patch": final_patch, "box": poly_bbox})

                # Now, attempt to remove the text using the AI inpainting service.
                try:
                    logger.info("Attempting to remove text using AI inpainting.")
                    combined_mask = Image.new("L", original_image.size, 0)
                    draw_mask = ImageDraw.Draw(combined_mask)
                    for region in ocr_result.regions:
                        draw_mask.polygon(region.bounding_box, fill=255)

                    image_to_inpaint_rgb = original_image.convert("RGB")
                    image_to_inpaint_url_obj = await self._upload_image_to_storage(
                        image_to_inpaint_rgb
                    )
                    mask_url_obj = await self._upload_image_to_storage(combined_mask)

                    removed_text_image_url = (
                        await self.replicate_artwork_service.remove_object_using_mask(
                            input_image_url=image_to_inpaint_url_obj.image_url,
                            mask_image_url=mask_url_obj.image_url,
                        )
                    )

                    removed_text_image_bytes = await self._download_image(
                        removed_text_image_url
                    )
                    original_image = Image.open(removed_text_image_bytes).convert(
                        "RGBA"
                    )
                    logger.info("Successfully removed text using AI.")

                except Exception as e:
                    logger.error(
                        "Failed to remove text using AI, falling back to average color fill: %s",
                        e,
                        exc_info=True,
                    )
                    # Fallback: Fill the text area in the main image with the average color.
                    avg_color = self._get_average_color(original_image)
                    draw = ImageDraw.Draw(original_image)
                    for region in ocr_result.regions:
                        draw.polygon(region.bounding_box, fill=avg_color)
        # --- End of text handling ---

        # Resize original image to the size of the bounding box
        original_image = original_image.resize(
            (request.original_box.width, request.original_box.height)
        )

        # Create a new canvas with target dimensions
        canvas = Image.new(
            "RGBA", (request.target_width, request.target_height), (0, 0, 0, 0)
        )
        # Paste the original image into the bounding box, using the image's alpha channel as a mask
        canvas.paste(
            original_image,
            (request.original_box.x, request.original_box.y),
            original_image,
        )

        initial_box = [
            request.original_box.x,
            request.original_box.y,
            request.original_box.x + request.original_box.width,
            request.original_box.y + request.original_box.height,
        ]

        # If the initial image already covers the target area, just crop and return.
        if self._is_target_dimension_reached(
            initial_box, request.target_width, request.target_height
        ):
            logger.info(
                "Initial image already covers target dimensions. Cropping and returning."
            )
            cropped_canvas = canvas.crop(
                (0, 0, request.target_width, request.target_height)
            )
            return await self._upload_image_to_storage(cropped_canvas)

        current_box = initial_box
        original_image_area = request.original_box.width * request.original_box.height
        max_extension_area = int(original_image_area * 0.6)

        current_image = canvas
        max_iterations = 20
        iterations = 0

        logger.info(
            f"Starting extension loop. Max iterations: {max_iterations}, Max extension area per step: {max_extension_area}px"
        )

        while (
            not self._is_target_dimension_reached(
                current_box, request.target_width, request.target_height
            )
            and iterations < max_iterations
        ):
            iterations += 1
            logger.info(
                f"Iteration {iterations}/{max_iterations} | Current box: {current_box}"
            )

            (
                expansion_box,
                mask_for_inpaint,
                context_image_for_inpaint,
            ) = self._prepare_iteration(
                current_box,
                request.target_width,
                request.target_height,
                max_extension_area,
                current_image,
                request.invert_text,
            )

            logger.info(f"Expansion box for iteration {iterations}: {expansion_box}")

            if expansion_box == current_box:
                logger.warning(
                    "Expansion stalled as expansion box is same as current box. Exiting loop."
                )
                break

            try:
                mask_url = await self._upload_image_to_storage(mask_for_inpaint)
                image_url = await self._upload_image_to_storage(
                    context_image_for_inpaint
                )

                logger.info("Invoking inpainting service...")
                inpainted_image_url = (
                    await self.replicate_artwork_service.inpaint_image_using_ideogram(
                        image_url=image_url.image_url,
                        mask_url=mask_url.image_url,
                        prompt=background_prompt.background_prompt,
                    )
                )
                inpainted_image_bytes = await self._download_image(inpainted_image_url)
                inpainted_image = Image.open(inpainted_image_bytes).convert("RGBA")

                # The inpainted image should be the same size as the context image for inpainting
                if inpainted_image.size != context_image_for_inpaint.size:
                    logger.warning(
                        f"Inpainted image size {inpainted_image.size} does not match context size {context_image_for_inpaint.size}. Resizing."
                    )
                    inpainted_image = inpainted_image.resize(
                        context_image_for_inpaint.size
                    )

                # Paste the inpainted part onto the main canvas
                current_image.paste(
                    inpainted_image,
                    (expansion_box[0], expansion_box[1]),
                    inpainted_image,
                )

                current_box = self._calculate_new_bounding_box(
                    current_box, expansion_box
                )
                logger.info(
                    f"Iteration {iterations} successful. New box: {current_box}"
                )

            except Exception as e:
                logger.error(
                    f"Error during inpainting step {iterations}: {e}", exc_info=True
                )
                break

        if self._is_target_dimension_reached(
            current_box, request.target_width, request.target_height
        ):
            logger.info(
                f"Successfully extended image to target dimensions in {iterations} iterations."
            )
        else:
            logger.warning(
                f"Failed to extend image to full target dimensions after {iterations} iterations. Returning current result."
            )

        # --- Restore Text ---
        if saved_text_patches:
            logger.info(f"Restoring {len(saved_text_patches)} text patches.")
            scale_x = request.original_box.width / original_image_with_text.width
            scale_y = request.original_box.height / original_image_with_text.height

            for item in saved_text_patches:
                patch_img = item["patch"]
                original_box = item["box"]

                new_width = int(patch_img.width * scale_x)
                new_height = int(patch_img.height * scale_y)

                if new_width == 0 or new_height == 0:
                    continue

                resized_patch = patch_img.resize((new_width, new_height))

                # Calculate final position on the canvas
                paste_x = int(original_box[0] * scale_x) + request.original_box.x
                paste_y = int(original_box[1] * scale_y) + request.original_box.y

                current_image.paste(resized_patch, (paste_x, paste_y), resized_patch)
        # --- End of Restore Text ---

        # Save the final image to permanent storage
        final_image_io = BytesIO()
        current_image.save(final_image_io, format="PNG")
        final_image_io.seek(0)

        image_id = uuid.uuid4()
        metadata = UploadMetadata(
            artwork_type="extended_image",
            user_id=str(user.id),
            artwork_status="final",
            artwork_width=str(current_image.width),
            artwork_height=str(current_image.height),
        )

        image_path = f"users/{str(user.id)}/extended_image/{str(image_id)}"
        image_url = await upload_image_to_bucket(
            final_image_io.getvalue(), image_path, metadata
        )

        if not image_url:
            raise ValueError("Image could not be uploaded")

        return await add_extended_image(
            image_url=image_path,
            user=user,
        )

    def _get_average_color(self, image: Image.Image) -> tuple[int, int, int, int]:
        """Calculates the average color of a PIL image."""
        # Convert to RGBA to ensure a consistent color format
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Resize to 1x1 pixel to get the average color
        avg_image = image.resize((1, 1), Image.Resampling.LANCZOS)
        pixel = avg_image.getpixel((0, 0))

        if isinstance(pixel, tuple) and len(pixel) == 4:
            return pixel
        elif isinstance(pixel, tuple) and len(pixel) == 3:
            return (pixel[0], pixel[1], pixel[2], 255)
        elif isinstance(pixel, int):
            return (pixel, pixel, pixel, 255)
        else:
            # Fallback for unexpected formats
            return (0, 0, 0, 0)

    def _get_bounding_box_for_polygon(
        self, polygon_coords: list[float]
    ) -> tuple[int, int, int, int]:
        """Calculates the bounding box for a polygon given as a list of coordinates."""
        x_coords = polygon_coords[0::2]
        y_coords = polygon_coords[1::2]
        min_x = int(min(x_coords))
        min_y = int(min(y_coords))
        max_x = int(max(x_coords))
        max_y = int(max(y_coords))
        return min_x, min_y, max_x, max_y

    def _is_target_dimension_reached(self, box, target_width, target_height):
        return (
            box[0] <= 0
            and box[1] <= 0
            and box[2] >= target_width
            and box[3] >= target_height
        )

    def _prepare_iteration(
        self,
        current_box,
        target_w,
        target_h,
        max_area,
        current_image,
        invert_mask: bool = False,
    ):
        step = 10
        expansion_box = list(current_box)
        area_at_start = (current_box[2] - current_box[0]) * (
            current_box[3] - current_box[1]
        )

        # Greedily expand the box by `step` pixels on all sides until the new area added
        # exceeds `max_area`.
        while True:
            # Calculate next potential expansion
            next_x1 = max(0, expansion_box[0] - step)
            next_y1 = max(0, expansion_box[1] - step)
            next_x2 = min(target_w, expansion_box[2] + step)
            next_y2 = min(target_h, expansion_box[3] + step)
            next_box = [next_x1, next_y1, next_x2, next_y2]

            # If the box cannot expand further, we've hit the canvas edges.
            if next_box == expansion_box:
                break

            new_area = (next_box[2] - next_box[0]) * (next_box[3] - next_box[1])

            # If this expansion is too large, we stop here.
            # expansion_box has the last valid value.
            if area_at_start > 0 and (new_area - area_at_start) > max_area:
                break

            expansion_box = next_box

            # If we've reached the target dimensions, expansion is complete.
            if expansion_box == [0, 0, target_w, target_h]:
                break

        context_image_for_inpaint = current_image.crop(expansion_box)

        # Per the requirement: Black will be ignored (preserved), and White will be filled.

        if invert_mask:
            # Inverted: preserved area is white (255), filled area is black (0)
            mask_bg_color, preserved_area_fill_color = 0, 255
        else:
            # Default: preserved area is black (0), filled area is white (255)
            mask_bg_color, preserved_area_fill_color = 255, 0

        # 1. Create a white mask. By default, everything is marked to be filled.
        mask = Image.new("L", context_image_for_inpaint.size, mask_bg_color)
        draw = ImageDraw.Draw(mask)

        # 2. Determine which sides are being extended.
        is_extending_left = expansion_box[0] < current_box[0]
        is_extending_right = expansion_box[2] > current_box[2]
        is_extending_top = expansion_box[1] < current_box[1]
        is_extending_bottom = expansion_box[3] > current_box[3]

        # 3. Calculate dynamic context overlap for each side.
        max_overlap_x = max(5, int((current_box[2] - current_box[0]) * 0.05))
        max_overlap_y = max(5, int((current_box[3] - current_box[1]) * 0.05))

        overlap_left = max_overlap_x if is_extending_left else 0
        overlap_right = max_overlap_x if is_extending_right else 0
        overlap_top = max_overlap_y if is_extending_top else 0
        overlap_bottom = max_overlap_y if is_extending_bottom else 0

        # 4. Calculate the preserved area inside the current image box.
        # This is the area that will NOT be touched by the AI.
        preserved_area = [
            (current_box[0] - expansion_box[0]) + overlap_left,
            (current_box[1] - expansion_box[1]) + overlap_top,
            (current_box[2] - expansion_box[0]) - overlap_right,
            (current_box[3] - expansion_box[1]) - overlap_bottom,
        ]

        # 5. Draw the black rectangle for the preserved area on the white mask.
        if (
            preserved_area[0] < preserved_area[2]
            and preserved_area[1] < preserved_area[3]
        ):
            draw.rectangle(preserved_area, fill=preserved_area_fill_color)

        return expansion_box, mask, context_image_for_inpaint

    def _calculate_new_bounding_box(self, current_box, expansion_box):
        return expansion_box

    async def _upload_image_to_storage(self, image: Image.Image) -> CoverArtSchema:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        object_name = await upload_temp_file_to_bucket(buffer.getvalue(), suffix=".png")
        if not object_name:
            raise Exception("Failed to upload image to storage")
        url = get_user_generated_url_for_object(object_name)

        # Create a temporary CoverArtSchema for the intermediate upload
        return CoverArtSchema(
            id=str(uuid.uuid4()),
            book_id="",  # This is temporary and will be replaced
            image_url=url,
            image_width=image.width,
            image_height=image.height,
            created_at=datetime.datetime.now(),
        )

    async def _download_image(self, url: str) -> BytesIO:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=60.0)
                response.raise_for_status()
                return BytesIO(response.content)
            except httpx.RequestError as e:
                logger.error(f"Error downloading image from {url}: {e}")
                raise


def get_extend_image_service(
    replicate_artwork_service: ReplicateArtworkService = Depends(
        get_replicate_artwork_service
    ),
    background_analyser_service: BackgroundAnalyserService = Depends(
        get_background_analyser_service
    ),
) -> ExtendImageService:
    return ExtendImageService(
        replicate_artwork_service=replicate_artwork_service,
        background_analyser_service=background_analyser_service,
    )
