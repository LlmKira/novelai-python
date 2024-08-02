# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午3:05
# @Author  : sudoskys
# @File    : ApiToken.py
# @Software: PyCharm

from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import SecretStr, Field, field_validator

from ._base import CredentialBase, FAKE_UA


class ApiCredential(CredentialBase):
    """
    ApiCredential is the base class for all credential.
    """
    api_token: SecretStr = Field(None, description="api token")

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": FAKE_UA.edge,
            "Authorization": f"Bearer {self.api_token.get_secret_value()}",
            "Content-Type": "application/json",
            "Origin": "https://novelai.net",
            "Referer": "https://novelai.net/",
        }

        if update_headers:
            assert isinstance(update_headers, dict), "update_headers must be a dict"
            headers.update(update_headers)

        return AsyncSession(timeout=timeout, headers=headers, impersonate="edge101")

    @field_validator('api_token')
    def check_api_token(cls, v: SecretStr):
        if not v.get_secret_value().startswith("pst"):
            logger.warning("api token should start with pst-")
        return v
