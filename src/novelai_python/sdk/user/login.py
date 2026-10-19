# @Time    : 2024/2/7 上午11:46
# @Author  : sudoskys
# @File    : login.py

import json
import logging

import curl_cffi
from curl_cffi.requests import AsyncSession
from pydantic import Field, PrivateAttr

from ..._exceptions import APIError, SessionHttpError
from ..._response.user.login import LoginResp
from ...credential import CredentialBase
from ...credential._base import IMPERSONATE, _correlation_id, _initiated_at, browser_headers
from ...utils import encode_access_key
from ..schema import ApiBaseModel, use_session

logger = logging.getLogger(__name__)


class Login(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    key: str = Field(..., description="User's key")
    recaptcha: str | None = Field(default=None, description="reCAPTCHA token, as the web client sends it")
    _proxy: str | None = PrivateAttr(default=None)
    """Outbound proxy for the login request, set only by ``Login.build(proxy=...)``: a request body
    (the server's /user/login) must not choose where the server connects."""
    measure_id: str | None = Field(default=None, exclude=True)
    """
    FingerprintJS event_id the web client sends as ``x-measure-id``. The client leaves the header
    out when the agent fails to load (e.g. blocked by an ad blocker), so it is optional. Pass one
    only if it comes from a real browser session: a made-up id does not exist on the server side.
    """

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/login"

    @property
    def session(self):
        kw: dict = {}
        if self._proxy:
            kw["proxies"] = {"http": self._proxy, "https": self._proxy}
        return AsyncSession(
            timeout=180,
            headers=browser_headers({"Content-Type": "application/json"}),
            impersonate=IMPERSONATE,
            trust_env=False,  # never route through a system HTTP(S)_PROXY by accident
            **kw,
        )

    @classmethod
    def build(
        cls,
        *,
        user_name: str,
        password: str,
        recaptcha: str | None = None,
        measure_id: str | None = None,
        proxy: str | None = None,
    ):
        """
        From username and password to build a Login instance
        :param user_name: account email
        :param password:
        :param recaptcha: optional reCAPTCHA token
        :param measure_id: optional FingerprintJS event_id from a real browser (see ``measure_id``)
        :param proxy: outbound proxy for the login request
        :return:
        """
        login = cls(key=encode_access_key(user_name, password), recaptcha=recaptcha, measure_id=measure_id)
        login._proxy = proxy
        return login

    async def request(
        self,
        session: AsyncSession | CredentialBase | None = None,
        *,
        override_headers: dict | None = None,
    ) -> LoginResp:
        """
        Request to get user access token
        :return:
        """
        # Data Build
        request_data = self.model_dump(mode="json", exclude_none=True)
        # errors carry the request; the key is derived from the password, keep it out of them
        logged_request = {**request_data, "key": "<redacted>"}

        if isinstance(session, AsyncSession):
            context = use_session(session)  # the caller's session stays open
        elif isinstance(session, CredentialBase):
            # the credential's proxy, not its get_session(): that one may log in itself
            context = AsyncSession(**session.session_kwargs(180, browser_headers({"Content-Type": "application/json"})))
        else:
            context = self.session
        async with context as sess:
            # Header
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            logger.debug("Fetching login-credential")
            try:
                # per-request headers in the web client's order
                headers = {"x-correlation-id": _correlation_id(), "x-initiated-at": _initiated_at()}
                if self.measure_id:
                    headers["x-measure-id"] = self.measure_id
                response = await sess.post(
                    self.base_url, data=json.dumps(request_data).encode("utf-8"), headers=headers
                )
                content_type = response.headers.get("Content-Type") or ""
                if "application/json" not in content_type or response.status_code != 201:
                    error_message = await self.handle_error_response(response=response, request_data=logged_request)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400, 401]:
                        # 400 : A validation error occured.
                        # 401 : Access Key is incorrect.
                        raise APIError(message, request=logged_request, code=status_code, response=error_message)
                    if status_code in [500]:
                        # An unknown error occured.
                        raise APIError(message, request=logged_request, code=status_code, response=error_message)
                    raise APIError(message, request=logged_request, code=status_code, response=error_message)
                return LoginResp.model_validate_json(response.content)
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, maybe SSL error. Try again later!"
                ) from exc
            except APIError:
                raise  # not an unexpected error: keep it out of the handler below
            except Exception as e:
                logger.exception("An Unexpected error occurred")
                raise e
