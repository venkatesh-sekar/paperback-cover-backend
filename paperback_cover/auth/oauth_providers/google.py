from typing import Any, cast

from httpx_oauth.clients.google import PROFILE_ENDPOINT, GoogleOAuth2
from httpx_oauth.exceptions import GetProfileError

from paperback_cover.auth.oauth_providers.base import BaseOauth2Provider, OauthUserName


class GoogleOauth2Provider(GoogleOAuth2, BaseOauth2Provider):
    async def get_profile(self, token: str) -> dict[str, Any]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                PROFILE_ENDPOINT,
                params={"personFields": "names,emailAddresses"},
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetProfileError(response=response)

            return cast(dict[str, Any], response.json())

    async def get_user_first_and_last_name(self, token: str) -> OauthUserName:
        profile = await self.get_profile(token=token)

        first_name = ""
        last_name = ""

        names = profile.get("names", [])
        primary_name = next(
            (name for name in names if name.get("metadata", {}).get("primary", False)),
            {},
        )

        first_name = primary_name.get("givenName", "")
        last_name = primary_name.get("familyName", "")

        if not first_name or not last_name:
            display_name = primary_name.get("displayName", "")
            if display_name:
                name_parts = display_name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:])
                elif len(name_parts) == 1:
                    first_name = name_parts[0]

        return OauthUserName(first_name=first_name, last_name=last_name)
