# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:09
# @Author  : sudoskys
# @File    : suggest-tags.py
# @Software: PyCharm
from typing import Optional, Union
from urllib.parse import urlparse

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import PrivateAttr

from ._enum import Model
from ...schema import ApiBaseModel
from ...._exceptions import APIError, AuthError, SessionHttpError
from ...._response.ai.generate_image import SuggestTagsResp
from ....credential import CredentialBase
from ....utils import try_jsonfy


class SuggestTags(ApiBaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")
    model: Model = Model.NAI_DIFFUSION_3
    prompt: str = "landscape"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate-image/suggest-tags"

    async def necessary_headers(self, request_data) -> dict:
        return {
            "Host": urlparse(self.endpoint).netloc,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Access-Control-Allow-Origin": "*",
            "Referer": "https://novelai.net/",
            "Content-Type": "application/json",
            "Origin": "https://novelai.net",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "TE": "trailers",
        }

    async def request(self,
                      session: Union[AsyncSession, CredentialBase],
                      *,
                      override_headers: Optional[dict] = None
                      ) -> SuggestTagsResp:
        """
        Request to get user subscription information
        :param override_headers:
        :param session:
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
        logger.debug("SuggestTags")
        try:
            assert hasattr(session, "get"), "session must have get method."
            response = await session.get(
                url=self.base_url + "?" + "&".join([f"{k}={v}" for k, v in request_data.items()])
            )
            if "application/json" not in response.headers.get('Content-Type') or response.status_code != 200:
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
                if status_code in [400, 401, 402]:
                    # 400 : validation error
                    # 401 : unauthorized
                    # 402 : payment required
                    # 409 : conflict
                    raise AuthError(message, request=request_data, code=status_code, response=_msg)
                if status_code in [500]:
                    # An unknown error occured.
                    raise APIError(message, request=request_data, code=status_code, response=_msg)
                raise APIError(message, request=request_data, code=status_code, response=_msg)
            return SuggestTagsResp.model_validate(response.json())
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
