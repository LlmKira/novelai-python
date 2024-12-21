# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : UserAuth.py
import time
from typing import Optional

import arrow
import shortuuid
from curl_cffi.requests import AsyncSession
from pydantic import SecretStr, Field

from ._base import CredentialBase, FAKE_UA


class LoginCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """
    username: str = Field(None, description="username")
    password: SecretStr = Field(None, description="password")
    session_headers: dict = Field(default_factory=dict)
    update_at: Optional[int] = None
    x_correlation_id: str = shortuuid.uuid()[0:6]

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        headers = {
            "Accept": "*/*",
            "User-Agent": FAKE_UA.edge,
            "Accept-Encoding": "gzip, deflate, br",
            "Authorization": "Bearer ",
            "Content-Type": "application/json",
            "Origin": "https://novelai.net",
            "Referer": "https://novelai.net/",
            "x-correlation-id": self.x_correlation_id,
            "x-initiated-at": f"{arrow.utcnow().isoformat()}Z",
        }

        # 30 天有效期
        if not self.session_headers or int(time.time()) - self.update_at > 29 * 24 * 60 * 60:
            from ..sdk import Login
            resp = await Login.build(user_name=self.username, password=self.password.get_secret_value()).request()
            headers["Authorization"] = f"Bearer {resp.accessToken}"
            self.session_headers = headers
            self.update_at = int(time.time())
        else:
            headers.update(self.session_headers)

        if update_headers:
            headers.update(update_headers)

        return AsyncSession(timeout=timeout, headers=headers, impersonate="edge101")
