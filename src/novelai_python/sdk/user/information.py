# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午3:09
# @Author  : sudoskys
# @File    : information.py

from typing import Optional, Union
from urllib.parse import urlparse

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import PrivateAttr

from ..schema import ApiBaseModel
from ..._exceptions import APIError, AuthError, SessionHttpError
from ..._response.user.information import InformationResp
from ...credential import CredentialBase


class Information(ApiBaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/user/information"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    async def request(self,
                      session: Union[AsyncSession, CredentialBase],
                      *,
                      override_headers: Optional[dict] = None
                      ) -> InformationResp:
        """
        Request to get user subscription information
        :param override_headers:
        :param session:
        :return: 
        """
        request_data = {}
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            # Header
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            logger.debug("Information")
            try:
                self.ensure_session_has_get_method(sess)
                response = await sess.get(
                    self.base_url
                )
                if "application/json" not in response.headers.get('Content-Type') or response.status_code != 200:
                    error_message = await self.handle_error_response(response=response, request_data=request_data)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400, 401, 402]:
                        # 400 : validation error
                        # 401 : unauthorized
                        # 402 : payment required
                        # 409 : conflict
                        raise AuthError(message, request=request_data, code=status_code, response=error_message)
                    if status_code in [500]:
                        # An unknown error occured.
                        raise APIError(message, request=request_data, code=status_code, response=error_message)
                    raise APIError(message, request=request_data, code=status_code, response=error_message)

                return InformationResp.model_validate(response.json())
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
