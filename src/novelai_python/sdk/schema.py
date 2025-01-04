# -*- coding: utf-8 -*-
# @Time    : 2024/2/10 上午11:15
# @Author  : sudoskys
# @File    : schema.py

from abc import ABC, abstractmethod
from typing import Optional, Union

from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import BaseModel, PrivateAttr

from ..credential import CredentialBase
from ..utils import try_jsonfy


class ApiBaseModel(BaseModel, ABC):
    _endpoint: Optional[str] = PrivateAttr()

    @property
    @abstractmethod
    def base_url(self):
        logger.error("ApiBaseModel.base_url must be overridden")
        return f"{self.endpoint.strip('/')}/need-to-override"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @abstractmethod
    async def necessary_headers(self, request_data) -> dict:
        raise NotImplementedError()

    @staticmethod
    def ensure_session_has_post_method(session):
        if not hasattr(session, "post"):
            raise AttributeError("SESSION_MUST_HAVE_POST_METHOD")

    @staticmethod
    def ensure_session_has_get_method(session):
        if not hasattr(session, "get"):
            raise AttributeError("SESSION_MUST_HAVE_GET_METHOD")

    async def handle_error_response(
            self,
            response,
            request_data: dict,
            content_hint: str = "Response content too long",
            max_content_length: int = 50
    ) -> dict:
        """
        Common method to handle error response
        :param response: HTTP response
        :param request_data: request data
        :param content_hint: hint for content too long
        :param max_content_length: max content length
        :return: dict of error message
        """
        logger.debug(
            f"\n[novelai-python] Unexpected response:\n"
            f"  - URL         : {self.base_url}\n"
            f"  - Content-Type: {response.headers.get('Content-Type', 'N/A')}\n"
            f"  - Status      : {response.status_code}\n"
        )
        try:
            # 尝试解析 JSON 响应
            error_message = response.json()
        except Exception as e:
            # 如果解析 JSON 失败，则记录日志，并尝试显示短内容
            logger.warning(f"Failed to parse error response: {e}")
            error_message = {
                "statusCode": response.status_code,
                "message": try_jsonfy(response.content)
                if len(response.content) < max_content_length
                else content_hint,
            }
        # 日志记录解析出的错误消息
        logger.trace(f"Parsed error message: {error_message}")
        return error_message

    @abstractmethod
    async def request(self,
                      session: Union[AsyncSession, CredentialBase],
                      *,
                      override_headers: Optional[dict] = None
                      ):
        raise NotImplementedError()
