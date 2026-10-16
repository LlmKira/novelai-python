# @Time    : 2024/2/7 上午11:46
# @Author  : sudoskys
# @File    : login.py

import json

import curl_cffi
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import Field, PrivateAttr

from ..._exceptions import APIError, SessionHttpError
from ..._response.user.login import LoginResp
from ...credential import CredentialBase
from ...credential._base import IMPERSONATE, browser_headers
from ...utils import encode_access_key
from ..schema import ApiBaseModel


class Login(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://api.novelai.net")
    key: str = Field(..., description="User's key")

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        self._endpoint = value

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/login"

    @property
    def session(self):
        return AsyncSession(
            timeout=180,
            headers=browser_headers(
                {
                    "Content-Type": "application/json",
                }
            ),
            impersonate=IMPERSONATE,
        )

    @classmethod
    def build(cls, *, user_name: str, password: str):
        """
        From username and password to build a Login instance
        :param user_name:
        :param password:
        :return:
        """
        return cls(key=encode_access_key(user_name, password))

    async def request(
        self,
        session: AsyncSession | CredentialBase = None,
        *,
        override_headers: dict | None = None,
    ) -> LoginResp:
        """
        Request to get user access token
        :return:
        """
        # Data Build
        request_data = self.model_dump(mode="json", exclude_none=True)

        async with session if isinstance(session, AsyncSession) else self.session as sess:
            # Header
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            logger.debug("Fetching login-credential")
            try:
                self.ensure_session_has_post_method(sess)
                response = await sess.post(self.base_url, data=json.dumps(request_data).encode("utf-8"))
                if "application/json" not in response.headers.get("Content-Type") or response.status_code != 201:
                    error_message = await self.handle_error_response(response=response, request_data=request_data)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400, 401]:
                        # 400 : A validation error occured.
                        # 401 : Access Key is incorrect.
                        raise APIError(message, request=request_data, code=status_code, response=error_message)
                    if status_code in [500]:
                        # An unknown error occured.
                        raise APIError(message, request=request_data, code=status_code, response=error_message)
                    raise APIError(message, request=request_data, code=status_code, response=error_message)
                return LoginResp.model_validate_json(response.content)
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, maybe SSL error. Try again later!"
                ) from exc
            except APIError as e:
                raise e
            except Exception as e:
                logger.opt(exception=e).exception("An Unexpected error occurred")
                raise e
