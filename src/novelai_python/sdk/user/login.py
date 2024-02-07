# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午11:46
# @Author  : sudoskys
# @File    : login.py
# @Software: PyCharm
import json
from typing import Optional

import httpx
from curl_cffi.requests import AsyncSession, RequestsError
from loguru import logger
from pydantic import BaseModel, PrivateAttr, Field

from ..._exceptions import APIError
from ..._response.user.login import LoginResp
from ...utils import try_jsonfy, encode_access_key


class Login(BaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")
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
        return AsyncSession(timeout=180, headers={
            "Content-Type": "application/json",
            "Origin": "https://novelai.net",
            "Referer": "https://novelai.net/",
        }, impersonate="chrome110")

    @classmethod
    def build(cls, *, user_name: str, password: str):
        """
        From username and password to build a Login instance
        :param user_name:
        :param password:
        :return:
        """
        return cls(key=encode_access_key(user_name, password))

    async def request(self,
                      ) -> LoginResp:
        """
        Request to get user access token
        :return:
        """
        request_data = self.model_dump(exclude_none=True)
        logger.debug("Login")
        try:
            assert hasattr(self.session, "post"), "session must have get method."
            response = await self.session.post(
                self.base_url,
                data=json.dumps(request_data).encode("utf-8")
            )
            if "application/json" not in response.headers.get('Content-Type') or response.status_code != 201:
                logger.error(f"Unexpected content type: {response.headers.get('Content-Type')}")
                try:
                    _msg = response.json()
                except Exception:
                    raise APIError(
                        message=f"Unexpected content type: {response.headers.get('Content-Type')}",
                        request=request_data,
                        status_code=response.status_code,
                        response=try_jsonfy(response.content)
                    )
                status_code = _msg.get("statusCode", response.status_code)
                message = _msg.get("message", "Unknown error")
                if status_code in [400, 401]:
                    # 400 : A validation error occured.
                    # 401 : Access Key is incorrect.
                    raise APIError(message, request=request_data, status_code=status_code, response=_msg)
                if status_code in [500]:
                    # An unknown error occured.
                    raise APIError(message, request=request_data, status_code=status_code, response=_msg)
                raise APIError(message, request=request_data, status_code=status_code, response=_msg)
            return LoginResp.model_validate(response.json())
        except RequestsError as exc:
            logger.exception(exc)
            raise RuntimeError(f"An AsyncSession error occurred: {exc}")
        except httpx.HTTPError as exc:
            raise RuntimeError(f"An HTTP error occurred: {exc}")
        except APIError as e:
            raise e
        except Exception as e:
            logger.opt(exception=e).exception("An Unexpected error occurred")
            raise e
