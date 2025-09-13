from google import genai

from paperback_cover.config import settings


class GeminiClient:
    """Client for interacting with Gemini API"""

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.google.fonts.api_key,
        )

    def get_client(self):
        return self.client
