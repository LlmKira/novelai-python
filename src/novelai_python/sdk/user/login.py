# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午11:46
# @Author  : sudoskys
# @File    : login.py
# @Software: PyCharm
import json
from typing import Optional, Union

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import PrivateAttr, Field

from ..schema import ApiBaseModel
from ..._exceptions import APIError, SessionHttpError
from ..._response.user.login import LoginResp
from ...credential import CredentialBase
from ...utils import try_jsonfy, encode_access_key


class Login(ApiBaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")
    _session: Optional[AsyncSession] = PrivateAttr(None)
    key: str = Field(..., description="User's key")

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/user/login"

    @property
    def session(self):
        if self._session is None:
            self._session = AsyncSession(timeout=180, headers={
                "Content-Type": "application/json",
                "Origin": "https://novelai.net",
                "Referer": "https://novelai.net/",
            }, impersonate="chrome110")
        return self._session

    @session.setter
    def session(self, value):
        if not isinstance(value, AsyncSession):
            raise ValueError("session must be an instance of AsyncSession")
        self._session = value

    @classmethod
    def build(cls, *, user_name: str, password: str):
        """
        From username and password to build a Login instance
        :param user_name:
        :param password:
        :return:
        """
        return cls(key=encode_access_key(user_name, password))

    async def necessary_headers(self, request_data) -> dict:
        return {}

    async def request(self,
                      session: Union[AsyncSession, CredentialBase] = None,
                      *,
                      override_headers: Optional[dict] = None,
                      ) -> LoginResp:
        """
        Request to get user access token
        :return:
        """
        # Data Build
        request_data = self.model_dump(mode="json", exclude_none=True)
        if isinstance(session, AsyncSession):
            session.headers.update(await self.necessary_headers(request_data))
        elif isinstance(session, CredentialBase):
            session = await session.get_session(update_headers=await self.necessary_headers(request_data))
        # Header
        if override_headers:
            session.headers.clear()
            session.headers.update(override_headers)
        logger.debug("Login")
        try:
            assert hasattr(self.session, "post"), "session must have get method."
            response = await self.session.post(
                self.base_url,
                data=json.dumps(request_data).encode("utf-8")
            )
            if "application/json" not in response.headers.get('Content-Type') or response.status_code != 201:
                logger.error(
                    f"Error with content type: {response.headers.get('Content-Type')} and code: {response.status_code}"
                )
                try:
                    _msg = response.json()
                except Exception as e:
                    logger.warning(e)
                    if not isinstance(response.content, str) and len(response.content) < 50:
                        raise APIError(
                            message=f"Unexpected content type: {response.headers.get('Content-Type')}",
                            request=request_data,
                            code=response.status_code,
                            response=try_jsonfy(response.content)
                        )
                    else:
                        _msg = {"statusCode": response.status_code, "message": response.content}
                status_code = _msg.get("statusCode", response.status_code)
                message = _msg.get("message", "Unknown error")
                if status_code in [400, 401]:
                    # 400 : A validation error occured.
                    # 401 : Access Key is incorrect.
                    raise APIError(message, request=request_data, code=status_code, response=_msg)
                if status_code in [500]:
                    # An unknown error occured.
                    raise APIError(message, request=request_data, code=status_code, response=_msg)
                raise APIError(message, request=request_data, code=status_code, response=_msg)
            return LoginResp.model_validate(response.json())
        except curl_cffi.requests.errors.RequestsError as exc:
            logger.exception(exc)
            raise SessionHttpError("An AsyncSession RequestsError occurred, maybe SSL error. Try again later!")
        except httpx.HTTPError as exc:
            logger.exception(exc)
            raise SessionHttpError("An HTTPError occurred, maybe SSL error. Try again later!")
        except APIError as e:
            raise e
        except Exception as e:
            logger.opt(exception=e).exception("An Unexpected error occurred")
            raise e
