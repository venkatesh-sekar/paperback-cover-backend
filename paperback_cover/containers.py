from paperback_cover.config import settings
from paperback_cover.cover_art.replicate_artwork_service import ReplicateArtworkService
from paperback_cover.imageedit.extend_image.service import ExtendImageService
from paperback_cover.imageedit.format_conversion.service import (
    ImageFormatConversionService,
)
from paperback_cover.openai.background_analyser_service import BackgroundAnalyserService
from paperback_cover.openai.final_prompt_optimiser_service import (
    FinalPromptOptimiserService,
)
from paperback_cover.openai.gemini_client import GeminiClient
from paperback_cover.openai.openai_client import OpenAiClient
from paperback_cover.replicate.replicateclient import ReplicateClient


class Container:
    openaiclient = OpenAiClient(api_key=settings.openai.api_key)
    geminiclient = GeminiClient()

    final_prompt_optimiser_service = FinalPromptOptimiserService(
        openai_client=openaiclient,
    )

    replicate_client = ReplicateClient(api_token=settings.replicate.api_token)
    replicate_artwork_service = ReplicateArtworkService(
        replicate_client=replicate_client,
    )

    background_analyser_service = BackgroundAnalyserService(
        openai_client=openaiclient,
    )

    extend_image_service = ExtendImageService(
        replicate_artwork_service=replicate_artwork_service,
        background_analyser_service=background_analyser_service,
    )

    image_format_conversion_service = ImageFormatConversionService()
