# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午10:04
# @Author  : sudoskys
# @File    : subscription.py.py
# @Software: PyCharm
from typing import Optional, Union

import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import BaseModel, PrivateAttr

from ... import APIError, AuthError
from ..._response.user.subscription import SubscriptionResp
from ...credential import JwtCredential
from ...utils import try_jsonfy


class Subscription(BaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/user/subscription"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    async def request(self,
                      session: Union[AsyncSession, JwtCredential],
                      ) -> SubscriptionResp:
        """
        Request to get user subscription information
        :param session: 
        :return: 
        """
        if isinstance(session, JwtCredential):
            session = session.session
        request_data = {}
        logger.debug("Subscription")
        try:
            assert hasattr(session, "get"), "session must have get method."
            response = await session.get(
                self.base_url,
            )
            if "application/json" not in response.headers.get('Content-Type'):
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
                if status_code in [400, 401, 402]:
                    # 400 : validation error
                    # 401 : unauthorized
                    # 402 : payment required
                    # 409 : conflict
                    raise AuthError(message, request=request_data, status_code=status_code, response=_msg)
                if status_code in [500]:
                    # An unknown error occured.
                    raise APIError(message, request=request_data, status_code=status_code, response=_msg)
                raise APIError(message, request=request_data, status_code=status_code, response=_msg)
            return SubscriptionResp.model_validate(response.json())
        except httpx.HTTPError as exc:
            raise RuntimeError(f"An HTTP error occurred: {exc}")
        except APIError as e:
            raise e
        except Exception as e:
            logger.opt(exception=e).exception("An Unexpected error occurred")
            raise e
