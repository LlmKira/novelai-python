# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : UserAuth.py
# @Software: PyCharm
import time
from typing import Optional

from curl_cffi.requests import AsyncSession
from pydantic import SecretStr, Field

from ._base import CredentialBase


class LoginCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """
    username: str = Field(None, description="username")
    password: SecretStr = Field(None, description="password")
    _session: Optional[AsyncSession] = None
    _update_at: Optional[int] = None

    async def get_session(self, timeout: int = 180):
        # 30 天有效期
        if not self._session or int(time.time()) - self._update_at > 29 * 24 * 60 * 60:
            from ..sdk import Login
            resp = await Login.build(user_name=self.username, password=self.password.get_secret_value()).request()
            self._session = AsyncSession(timeout=timeout, headers={
                "Authorization": f"Bearer {resp.accessToken}",
                "Content-Type": "application/json",
                "Origin": "https://novelai.net",
                "Referer": "https://novelai.net/",
            }, impersonate="chrome110")
            self._update_at = int(time.time())
        return self._session
