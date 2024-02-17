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
    JwtCredential is the base class for all credential.
    """
    api_token: SecretStr = Field(None, description="api token")
    _session: AsyncSession = None

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        if update_headers is None:
            update_headers = {}
        if not self._session:
            self._session = AsyncSession(timeout=timeout, headers={
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": FAKE_UA.edge,
                "Authorization": f"Bearer {self.api_token.get_secret_value()}",
                "Content-Type": "application/json",
                "Origin": "https://novelai.net",
                "Referer": "https://novelai.net/",
            }, impersonate="edge101")
        self._session.headers.update(update_headers)
        return self._session

    @field_validator('api_token')
    def check_api_token(cls, v: SecretStr):
        if not v.get_secret_value().startswith("pst"):
            logger.warning("api token should start with pst-")
        return v
