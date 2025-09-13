import logging
from typing import Optional

from fastapi import Depends
from pydantic import BaseModel

from paperback_cover.openai.openai_client import OpenAiClient, get_openai_client

logger = logging.getLogger(__name__)

INSTRUCTION = """
OBJECTIVE:
Your goal is to analyse the image given and give a detailed description of the background.

- Do not analyse any text. You should only explain the background artwork.
- The output should only describe the artwork, colors, style.
- Everything should be in one paragraph.
- The output is a prompt that would be directly used to generate just the background.

Example:
Dramatic, fiery landscape dominated by a massive black dragon with glowing red cracks along its body, giving it a molten, lava-like appearance. The dragon's wings are spread wide against a vivid, burning sunset sky, filled with intense shades of orange, red, and deep shadows, suggesting destruction and chaos. The ground is barren and cracked, scattered with jagged, dark rock formations and debris, as if a great battle or cataclysmic event has taken place. A glowing, runic sword is embedded in the ground, surrounded by flames, adding to the atmosphere of danger and mystical energy. The overall scene exudes an apocalyptic fantasy vibe, filled with tension and power.
"""


class OpenAiBackgroundAnalyserOutput(BaseModel):
    background_prompt: str


class BackgroundAnalyserService:
    client: OpenAiClient
    name = "Background analyser assistant"

    def __init__(self, openai_client: OpenAiClient):
        self.client = openai_client
        # With chat completions, there's no need to manage a separate assistant instance.

    async def anlayse_background(
        self, image_url: str
    ) -> Optional[OpenAiBackgroundAnalyserOutput]:
        # Build a content payload with the book data and image URL.
        content_payload = [
            {
                "type": "text",
                "text": "Analyse this image and give a detailed description of the background.  ",
            },
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

        completion = await self.client.get_client().beta.chat.completions.parse(
            model="google/gemini-flash-1.5",  # Ensure this model suits your needs.
            messages=[
                {"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": content_payload},
            ],
            response_format=OpenAiBackgroundAnalyserOutput,
        )
        message = completion.choices[0].message

        if message.parsed:
            logger.info(
                f"Successfully analysed the cover background | result: {message.parsed}"
            )
            return message.parsed
        else:
            logger.error("Failed to analyse cover background")
            return None


def get_background_analyser_service(
    openai_client: OpenAiClient = Depends(get_openai_client),
) -> BackgroundAnalyserService:
    return BackgroundAnalyserService(
        openai_client=openai_client,
    )
