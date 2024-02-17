# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : UserAuth.py
# @Software: PyCharm
import time
from typing import Optional

from curl_cffi.requests import AsyncSession
from pydantic import SecretStr, Field

from ._base import CredentialBase, FAKE_UA


class LoginCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """
    username: str = Field(None, description="username")
    password: SecretStr = Field(None, description="password")
    _session: Optional[AsyncSession] = None
    _update_at: Optional[int] = None

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        if update_headers is None:
            update_headers = {}
        # 30 天有效期
        if not self._session or int(time.time()) - self._update_at > 29 * 24 * 60 * 60:
            from ..sdk import Login
            resp = await Login.build(user_name=self.username, password=self.password.get_secret_value()).request()
            self._session = AsyncSession(timeout=timeout, headers={
                "Accept": "*/*",
                "User-Agent": FAKE_UA.edge,
                "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                "Accept-Encoding": "gzip, deflate, br",
                "Authorization": f"Bearer {resp.accessToken}",
                "Content-Type": "application/json",
                "Origin": "https://novelai.net",
                "Referer": "https://novelai.net/",
            }, impersonate="edge101")
            self._update_at = int(time.time())
        self._session.headers.update(update_headers)
        return self._session
