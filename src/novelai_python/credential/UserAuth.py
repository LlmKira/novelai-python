# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : UserAuth.py
import time

from curl_cffi.requests import AsyncSession
from pydantic import Field, SecretStr

from ._base import CredentialBase, _correlation_id, _initiated_at, browser_headers


class LoginCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """

    username: str | None = Field(default=None, description="username")
    password: SecretStr | None = Field(default=None, description="password")
    session_headers: dict = Field(default_factory=dict)
    update_at: int | None = None
    x_correlation_id: str = Field(default_factory=_correlation_id)

    async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
        headers = browser_headers(
            {
                "Authorization": "Bearer ",
                "Content-Type": "application/json",
                "x-correlation-id": self.x_correlation_id,
                "x-initiated-at": _initiated_at(),
            }
        )

        # 30 天有效期
        if not self.session_headers or self.update_at is None or int(time.time()) - self.update_at > 29 * 24 * 60 * 60:
            from ..sdk import Login

            # log in through the same proxy / fingerprint as every later request
            login_session = AsyncSession(
                **self.session_kwargs(timeout, browser_headers({"Content-Type": "application/json"}))
            )
            if not self.username or self.password is None:
                raise ValueError("LoginCredential needs username and password")
            resp = await Login.build(user_name=self.username, password=self.password.get_secret_value()).request(
                login_session
            )
            headers["Authorization"] = f"Bearer {resp.accessToken}"
            self.session_headers = headers
            self.update_at = int(time.time())
        else:
            headers.update(self.session_headers)

        if update_headers:
            headers.update(update_headers)

        return AsyncSession(**self.session_kwargs(timeout, headers))
