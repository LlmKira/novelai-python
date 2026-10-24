# @Time    : 2024/2/10 上午11:15
# @Author  : sudoskys
# @File    : schema.py

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Coroutine
from contextlib import asynccontextmanager
from typing import Any, ClassVar, Literal, NoReturn

import curl_cffi
from curl_cffi.requests import AsyncSession, Response
from pydantic import BaseModel, PrivateAttr

from .._exceptions import APIError, AuthError, ConcurrentGenerationError, SessionHttpError
from ..credential import CredentialBase
from ..metrics import _Observation, get_metrics
from ..utils import try_jsonfy

logger = logging.getLogger(__name__)


@asynccontextmanager
async def use_session(session: AsyncSession | CredentialBase) -> AsyncGenerator[AsyncSession]:
    """The session for one request. A caller's AsyncSession stays open: it may be reused, e.g. by a
    retry. A session made from a credential is closed when the request is done."""
    if isinstance(session, AsyncSession):
        yield session
        return
    async with await session.get_session() as sess:
        yield sess


@asynccontextmanager
async def observed_session(
    session: AsyncSession | CredentialBase, url: str, model: object | None = None
) -> AsyncGenerator[tuple[AsyncSession, _Observation]]:
    """The session for one request and its metrics observation, in one seam.

    The caller performs the request through ``observed.send(...)``, which reports the HTTP status;
    the observation then covers the response, and the whole stream for a ``stream=True`` call.
    """
    async with use_session(session) as sess, get_metrics().observe(url, model) as observed:
        yield sess, observed


async def close_stream(response: Response) -> None:
    """End a ``stream=True`` response, also when the caller stopped reading early.

    curl_cffi's ``aclose`` only waits for the transfer to finish; with ``quit_now`` set the next
    chunk aborts it, so the server stops generating and the handle goes back to the session pool.
    """
    if response.quit_now is not None:
        response.quit_now.set()
    await response.aclose()


class ApiBaseModel(BaseModel, ABC):
    _endpoint: str = PrivateAttr("")
    _legacy_400_as_auth: ClassVar[bool] = True
    """The older endpoints raise AuthError for a 400 validation error; newer ones set False (APIError)."""

    @property
    @abstractmethod
    def base_url(self) -> str:
        logger.error("ApiBaseModel.base_url must be overridden")
        return f"{self.endpoint.strip('/')}/need-to-override"

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        self._endpoint = value

    @property
    def metrics_model(self) -> Any:
        """Model label for the metrics; subclasses with a ``model`` field inherit it from here."""
        return getattr(self, "model", None)

    async def handle_error_response(
        self,
        response,
        request_data: dict,
        content_hint: str = "Response content too long",
        max_content_length: int = 50,
        stream: bool = False,
    ) -> dict:
        """
        Common method to handle error response
        :param response: HTTP response
        :param request_data: request data
        :param content_hint: hint for content too long
        :param max_content_length: max content length
        :param stream: the response was opened with ``stream=True``; its body is read here,
            because ``response.content`` stays empty on a streamed response
        :return: dict of error message
        """
        logger.debug(
            f"\n[novelai-python] Unexpected response:\n"
            f"  - URL         : {self.base_url}\n"
            f"  - Content-Type: {response.headers.get('Content-Type', 'N/A')}\n"
            f"  - Status      : {response.status_code}\n"
        )
        content = b""
        try:
            # 尝试解析 JSON 响应
            if stream:
                content = await response.acontent()
                error_message = json.loads(content)
            else:
                content = response.content
                error_message = response.json()
        except Exception as e:
            # 如果解析 JSON 失败，则记录日志，并尝试显示短内容
            logger.warning(f"Failed to parse error response: {e}")
            error_message = {
                "statusCode": response.status_code,
                "message": try_jsonfy(content) if len(content) < max_content_length else content_hint,
            }
        # 日志记录解析出的错误消息
        logger.debug(f"Parsed error message: {error_message}")
        return error_message

    async def _send(
        self,
        session: AsyncSession | CredentialBase,
        method: Literal["GET", "POST"],
        *,
        json_body: dict | None = None,
        override_headers: dict | None = None,
    ) -> Response:
        """Send one request to ``self.base_url`` and map HTTP errors to the SDK exceptions.

        :return: the successful (2xx) response.
        :raises AuthError: 400 / 401 / 402.
        :raises ConcurrentGenerationError: 429.
        :raises APIError: any other error status.
        :raises SessionHttpError: transport error (SSL, timeout...).
        """
        request_data = json_body or {}
        async with observed_session(session, self.base_url, self.metrics_model) as (sess, observed):
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            try:
                response = await observed.send(sess, method, self.base_url, json=json_body)
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.") from exc
            if response.status_code >= 400:
                self._raise_for_status(response.status_code, response.content, request_data, self._legacy_400_as_auth)
        return response

    @staticmethod
    def _raise_for_status(status_code: int, content: bytes, request_data: dict, auth_on_400: bool = True) -> NoReturn:
        """Raise the SDK exception for an error response body (``{"statusCode", "message"}`` JSON or text)."""
        try:
            error_message = json.loads(content)
            if not isinstance(error_message, dict):
                raise ValueError
        except ValueError:
            error_message = {"statusCode": status_code, "message": content[:200].decode("utf-8", errors="replace")}
        code = error_message.get("statusCode", status_code)
        message = str(error_message.get("message", "Unknown error"))
        # 400 is a validation error; the older endpoints report it as AuthError and keep doing so
        if code in (401, 402) or (code == 400 and auth_on_400):
            raise AuthError(message, request=request_data, code=code, response=error_message)
        if code == 429:
            raise ConcurrentGenerationError(message, request=request_data, code=code, response=error_message)
        raise APIError(message, request=request_data, code=code, response=error_message)

    @abstractmethod
    def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> Coroutine[Any, Any, Any]:
        """Send the request; subclasses implement it as ``async def``."""
        raise NotImplementedError()
