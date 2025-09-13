from openai import AsyncOpenAI, OpenAI

from paperback_cover.config import settings

OPEN_ROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenAiClient:
    client: AsyncOpenAI
    sync_client: OpenAI

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=OPEN_ROUTER_BASE_URL)
        self.sync_client = OpenAI(api_key=api_key, base_url=OPEN_ROUTER_BASE_URL)

    def get_client(self):
        return self.client

    def get_sync_client(self):
        return self.sync_client


def get_openai_client() -> OpenAiClient:
    return OpenAiClient(api_key=settings.openai.api_key)
