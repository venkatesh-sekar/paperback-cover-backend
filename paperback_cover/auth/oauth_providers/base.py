from httpx_oauth.oauth2 import BaseOAuth2
from pydantic import BaseModel


class OauthUserName(BaseModel):
    first_name: str
    last_name: str


class BaseOauth2Provider(BaseOAuth2):

    async def get_user_first_and_last_name(self, token: str) -> OauthUserName:
        raise NotImplementedError
