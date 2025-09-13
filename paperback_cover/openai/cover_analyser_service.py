import logging
from typing import Optional

from pydantic import BaseModel

from paperback_cover.book.schema import BookSchema
from paperback_cover.openai.openai_client import OpenAiClient

logger = logging.getLogger(__name__)

INSTRUCTION = """
OBJECTIVE:
Your primary goal is to create a detailed image generation prompt for a new book cover. This prompt should merge the artistic style and composition of a provided reference image with the narrative elements from the book's details. The final output should be a single, descriptive paragraph (max 250 words) that can be used to generate a visually compelling and thematically relevant book cover.

You will receive supplementary JSON data about the book. Use this data to determine the content of the cover.

BOOK DETAILS:
You will be provided with the following information about the book in JSON format:
- `title`: The title of the book.
- `author_name`: The name of the author.
- `genre`: The main genre of the book.
- `sub_genre`: The sub-genre of the book.
- `micro_genre`: A more specific genre.
- `blurb`: A short description of the book's plot.
- `series_name`: The name of the series, if applicable.
- `additional_details`: Additional details about the book.

PROMPT CONSTRUCTION:
Your task is to synthesize information from two sources: the reference image and the book details.

1.  **Analyze the Reference Image for Style:**
    *   **Artistic Style & Mood:** Identify the overall style (e.g., photorealistic, minimalist, abstract, digital painting, watercolor) and the mood it creates (e.g., mysterious, romantic, action-packed).
    *   **Composition & Layout:** Observe the composition (framing, focal point, balance, use of negative space). How are elements arranged?
    *   **Color & Light:** Note the color palette (dominant colors, warm/cool tones, contrast) and lighting (hard/soft, natural/artificial).

2.  **Extract Narrative Elements from Book Details:**
    *   Read the `title`, `blurb`, and `additional_details` carefully.
    *   Identify the key characters, settings, objects, and themes that should be on the cover. These are the *subjects* of your new image.

3.  **Synthesize into a New Prompt:**
    *   Combine the artistic style from the image with the narrative elements from the book details.
    *   Describe a new scene. For example, if the image is a dark, moody photograph of a single person and the book is about a detective in a futuristic city, your prompt should describe the detective in that city, but captured with the dark, moody photographic style.
    *   Focus on creating a rich visual description.

GUIDELINES:
- **Create, Don't Analyze:** Your output is a creative prompt for a *new* image, not an analysis of the existing one.
- **Heavily Prioritize Book Details for Content:** The core subjects of the prompt (characters, setting, objects) must be drawn from the book details (`blurb`, `title`, `additional_details`).
- **Heavily Prioritize Image for Style:** The artistic direction (composition, color, light, medium) must be heavily inspired by the reference image.
- **IGNORE ALL TEXT:** Do not include any text, letters, or words in your generated prompt. Do not mention titles, author names, or logos. This is the most important rule.
- **Be Concise and Descriptive:** The output must be a single paragraph of no more than 250 words. It should be a rich, visual description of a scene.
"""


class OpenAiArtworkTemplaterOutput(BaseModel):
    prompt: str


class BookCoverAnalyserService:
    client: OpenAiClient
    name = "Cover analyser assistant"

    def __init__(self, openai_client: OpenAiClient):
        self.client = openai_client
        # With chat completions, there's no need to manage a separate assistant instance.

    async def anlayse_book_cover(
        self, image_url: str, book: BookSchema
    ) -> Optional[OpenAiArtworkTemplaterOutput]:
        # Build a content payload with the book data and image URL.
        content_payload = [
            {"type": "text", "text": book.model_dump_json()},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

        completion = await self.client.get_client().beta.chat.completions.parse(
            model="google/gemini-2.5-pro",  # Ensure this model suits your needs.
            messages=[
                {"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": content_payload},
            ],
            response_format=OpenAiArtworkTemplaterOutput,
        )
        message = completion.choices[0].message

        if message.parsed:
            logger.info(
                f"Successfully analysed the book cover | result: {message.parsed}"
            )
            return message.parsed
        else:
            logger.error("Failed to analyse book cover")
            return None
