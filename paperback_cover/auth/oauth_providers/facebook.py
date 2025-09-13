from typing import Any, cast

from httpx_oauth.clients.facebook import PROFILE_ENDPOINT, FacebookOAuth2
from httpx_oauth.exceptions import GetProfileError

from paperback_cover.auth.oauth_providers.base import BaseOauth2Provider, OauthUserName


class FacebookOauth2Provider(FacebookOAuth2, BaseOauth2Provider):

    async def get_profile(self, token: str) -> dict[str, Any]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                PROFILE_ENDPOINT,
                params={
                    "fields": "id,email,first_name,last_name",
                    "access_token": token,
                },
            )

            if response.status_code >= 400:
                raise GetProfileError(response=response)

            return cast(dict[str, Any], response.json())

    async def get_user_first_and_last_name(self, token: str) -> OauthUserName:
        profile = await self.get_profile(token=token)
        return OauthUserName(
            first_name=profile["first_name"],
            last_name=profile["last_name"],
        )
