import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page

from paperback_cover.auth.service import verify_active_user
from paperback_cover.commons.annotations import reduce_credits, timing
from paperback_cover.containers import Container
from paperback_cover.cover_art.schema import CoverArtInput, CoverArtSchema
from paperback_cover.cover_art.service import CoverArtService, fetch_artwork_generations
from paperback_cover.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cover_artworks",
    tags=["Cover Artworks"],
)


@router.get("/{book_id}")
@timing
async def fetch_all_artwork_generations_api(
    book_id: UUID,
    user: User = Depends(verify_active_user),
) -> Page[CoverArtSchema]:
    return await fetch_artwork_generations(user, book_id)


@router.post("")
@timing
@reduce_credits(6)
async def create_cover_art_endpoint(
    input: CoverArtInput,
    user: User = Depends(verify_active_user),
    cover_art_service: CoverArtService = Container.cover_art_service,
) -> CoverArtSchema | None:
    logger.info(f"Generating cover art for book {input.book_id} with input {input}")
    cover_output = await cover_art_service.generate_cover_art(input, user)
    return cover_output
