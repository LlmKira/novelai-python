# @Time    : 2024/1/26 上午11:04
# @Author  : sudoskys
# @File    : JwtToken.py


import logging

from curl_cffi.requests import AsyncSession
from pydantic import Field, SecretStr, field_validator

from ._base import CredentialBase, _correlation_id, _initiated_at, browser_headers

logger = logging.getLogger(__name__)


class JwtCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """

    jwt_token: SecretStr = Field(None, description="jwt token")
    x_correlation_id: str = Field(default_factory=_correlation_id)

    async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
        headers = browser_headers(
            {
                "Authorization": f"Bearer {self.jwt_token.get_secret_value()}",
                "Content-Type": "application/json",
                "x-correlation-id": self.x_correlation_id,
                "x-initiated-at": _initiated_at(),
            }
        )

        if update_headers:
            assert isinstance(update_headers, dict), "update_headers must be a dict"
            headers.update(update_headers)

        return AsyncSession(**self.session_kwargs(timeout, headers))

    @field_validator("jwt_token")
    def check_jwt_token(cls, v: SecretStr):
        if not v.get_secret_value().startswith("ey"):
            logger.warning("jwt_token should start with ey")
        return v
