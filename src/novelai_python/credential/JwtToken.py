# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午11:04
# @Author  : sudoskys
# @File    : JwtToken.py
# @Software: PyCharm
from curl_cffi.requests import AsyncSession
from pydantic import BaseModel, SecretStr, Field


class JwtCredential(BaseModel):
    """
    JwtCredential is the base class for all credential.
    """
    jwt_token: SecretStr = Field(None, description="jwt token")
    _session: AsyncSession = None

    @property
    def session(self, timeout: int = 180):
        if not self._session:
            self._session = AsyncSession(timeout=timeout, headers={
                "Authorization": f"Bearer {self.jwt_token.get_secret_value()}",
                "Content-Type": "application/json",
                "Origin": "https://novelai.net",
                "Referer": "https://novelai.net/",
            }, impersonate="chrome110")
        return self._session
