# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午11:04
# @Author  : sudoskys
# @File    : JwtToken.py
# @Software: PyCharm
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import SecretStr, Field, field_validator

from ._base import CredentialBase, FAKE_UA


class JwtCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """
    jwt_token: SecretStr = Field(None, description="jwt token")
    _session: AsyncSession = None

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        if update_headers is None:
            update_headers = {}
        if not self._session:
            self._session = AsyncSession(timeout=timeout, headers={
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                "User-Agent": FAKE_UA.edge,
                "Accept-Encoding": "gzip, deflate, br",
                "Authorization": f"Bearer {self.jwt_token.get_secret_value()}",
                "Content-Type": "application/json",
                "Origin": "https://novelai.net",
                "Referer": "https://novelai.net/",
            }, impersonate="edge101")
        assert isinstance(update_headers, dict), "update_headers must be a dict"
        self._session.headers.update(update_headers)
        return self._session

    @field_validator('jwt_token')
    def check_jwt_token(cls, v: SecretStr):
        if not v.get_secret_value().startswith("ey"):
            logger.warning("jwt_token should start with ey")
        return v
