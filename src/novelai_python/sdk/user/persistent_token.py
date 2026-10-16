# @File    : persistent_token.py

from curl_cffi.requests import AsyncSession
from pydantic import BaseModel, Field, PrivateAttr

from ...credential import CredentialBase
from ..schema import ApiBaseModel


class PersistentTokenResp(BaseModel):
    token: str = Field(..., description="Long-lived API key, sent as `Authorization: Bearer pst-...`")


class CreatePersistentToken(ApiBaseModel):
    """POST /user/create-persistent-token.

    Needs a JWT session (``JwtCredential`` / ``LoginCredential``): a request made
    with an existing persistent token is rejected. Without ``overwrite`` the API
    answers 409 if the account already has a token.
    """

    overwrite: bool = False
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/create-persistent-token"

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> PersistentTokenResp:
        """
        :raises APIError: code 409 when a token exists and ``overwrite`` is False.
        """
        response = await self._send(
            session, "POST", json_body={"overwrite": self.overwrite}, override_headers=override_headers
        )
        return PersistentTokenResp.model_validate_json(response.content)
