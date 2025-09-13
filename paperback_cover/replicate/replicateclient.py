import httpx
from replicate.client import Client

from paperback_cover.config import settings


class ReplicateClient:
    client: Client

    def __init__(self, api_token: str):
        self.client = Client(
            api_token=api_token,
            timeout=httpx.Timeout(180.0, connect=30.0),
        )

    def get_client(self):
        return self.client


def get_replicate_client() -> ReplicateClient:
    return ReplicateClient(api_token=settings.replicate.api_token)
