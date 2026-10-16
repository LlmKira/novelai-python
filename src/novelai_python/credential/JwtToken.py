# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午11:04
# @Author  : sudoskys
# @File    : JwtToken.py


from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import SecretStr, Field, field_validator

from ._base import _initiated_at, _correlation_id, CredentialBase, browser_headers, IMPERSONATE


class JwtCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """
    jwt_token: SecretStr = Field(None, description="jwt token")
    x_correlation_id: str = Field(default_factory=_correlation_id)

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        headers = browser_headers({
            "Authorization": f"Bearer {self.jwt_token.get_secret_value()}",
            "Content-Type": "application/json",
            "x-correlation-id": self.x_correlation_id,
            "x-initiated-at": _initiated_at(),
        })

        if update_headers:
            assert isinstance(update_headers, dict), "update_headers must be a dict"
            headers.update(update_headers)

        return AsyncSession(**self.session_kwargs(timeout, headers))

    @field_validator('jwt_token')
    def check_jwt_token(cls, v: SecretStr):
        if not v.get_secret_value().startswith("ey"):
            logger.warning("jwt_token should start with ey")
        return v