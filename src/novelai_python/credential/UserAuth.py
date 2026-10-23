# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : UserAuth.py
import asyncio
import time

from curl_cffi.requests import AsyncSession
from pydantic import Field, PrivateAttr, SecretStr

from ._base import CredentialBase, _correlation_id, _initiated_at, browser_headers


class _LoginSession(AsyncSession):
    """A session that drops the credential's cached token when NovelAI answers 401 to it."""

    def __init__(self, credential: "LoginCredential", **kwargs) -> None:
        super().__init__(**kwargs)
        self._credential = credential

    async def request(self, *args, **kwargs):  # pyright: ignore[reportIncompatibleMethodOverride]
        response = await super().request(*args, **kwargs)
        if response.status_code == 401:
            self._credential.forget_token(self.headers.get("authorization"))
        return response


class LoginCredential(CredentialBase):
    """
    JwtCredential is the base class for all credential.
    """

    username: str | None = Field(default=None, description="username")
    password: SecretStr | None = Field(default=None, description="password")
    session_headers: dict = Field(default_factory=dict, repr=False)  # holds the bearer token
    update_at: int | None = None
    x_correlation_id: str = Field(default_factory=_correlation_id)
    recaptcha: str | None = Field(default=None, description="Optional reCAPTCHA token for the login request")
    measure_id: str | None = Field(default=None, description="Optional FingerprintJS event_id (see Login)")
    _login_lock: asyncio.Lock | None = PrivateAttr(default=None)
    _login_lock_loop: asyncio.AbstractEventLoop | None = PrivateAttr(default=None)

    def _metrics_seed(self) -> str | None:
        return self.username

    def _token_expired(self) -> bool:
        # 30 天有效期
        return (
            not self.session_headers or self.update_at is None or int(time.time()) - self.update_at > 29 * 24 * 60 * 60
        )

    def forget_token(self, authorization: str | None = None) -> None:
        """Log in again on the next request. With ``authorization``, only if that is still the cached token
        (a session made before a newer login must not drop the newer token)."""
        if authorization is None or self.session_headers.get("authorization") == authorization:
            self.session_headers = {}
            self.update_at = None

    def _lock(self) -> asyncio.Lock:
        # an asyncio.Lock belongs to one event loop; a credential can outlive it (several asyncio.run)
        loop = asyncio.get_running_loop()
        if self._login_lock is None or self._login_lock_loop is not loop:
            self._login_lock, self._login_lock_loop = asyncio.Lock(), loop
        return self._login_lock

    async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
        if self._token_expired():
            # concurrent first requests log in once; the others wait for that token
            async with self._lock():
                if self._token_expired():
                    from ..sdk import Login

                    if not self.username or self.password is None:
                        raise ValueError("LoginCredential needs username and password")
                    resp = await Login.build(
                        user_name=self.username,
                        password=self.password.get_secret_value(),
                        recaptcha=self.recaptcha,
                        measure_id=self.measure_id,
                    ).request(self)  # logs in through this credential's proxy
                    # only the token is cached; the per-request headers are built fresh below
                    self.session_headers = {"authorization": f"Bearer {resp.accessToken}"}
                    self.update_at = int(time.time())

        headers = browser_headers(
            {
                **self.session_headers,
                "content-type": "application/json",
                "x-correlation-id": self.x_correlation_id,
                "x-initiated-at": _initiated_at(),
                **(update_headers or {}),
            }
        )
        return _LoginSession(self, **self.session_kwargs(timeout, headers))
