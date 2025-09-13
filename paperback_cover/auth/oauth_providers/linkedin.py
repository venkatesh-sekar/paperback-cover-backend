from typing import Any, Optional

from httpx_oauth.clients.linkedin import LinkedInOAuth2
from httpx_oauth.exceptions import GetIdEmailError, GetProfileError

from paperback_cover.auth.oauth_providers.base import BaseOauth2Provider, OauthUserName


class LinkedinOauth2Provider(LinkedInOAuth2, BaseOauth2Provider):

    async def get_profile(self, token: str) -> dict[str, Any]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetProfileError(response=response)

            return response.json()

    async def get_email(self, token: str) -> dict[str, Any]:
        """Override the old get_email method to use the new userinfo endpoint"""
        profile = await self.get_profile(token)
        # Return in a format that matches expected structure
        return {
            "email": profile.get("email", ""),
            "email_verified": profile.get("email_verified", False),
        }

    async def get_id_email(self, token: str) -> tuple[str, Optional[str]]:
        """Override the old get_id_email method to use the new userinfo endpoint"""
        try:
            profile = await self.get_profile(token)
        except GetProfileError as e:
            raise GetIdEmailError(response=e.response) from e

        user_id = profile.get("sub", "")  # 'sub' is the user ID in the new format
        user_email = profile.get("email")

        return user_id, user_email

    async def get_user_first_and_last_name(self, token: str) -> OauthUserName:
        profile = await self.get_profile(token=token)

        # LinkedIn now returns a simpler structure with given_name and family_name
        first_name = profile.get("given_name", "")
        last_name = profile.get("family_name", "")

        # Fallback to name field if given_name/family_name are not available
        if not first_name and not last_name:
            full_name = profile.get("name", "")
            if full_name:
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:])
                elif len(name_parts) == 1:
                    first_name = name_parts[0]

        return OauthUserName(
            first_name=first_name,
            last_name=last_name,
        )
