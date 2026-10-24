# @File    : openai_compat.py
"""OpenAI-compatible text API of text.novelai.net (``/oa/v1/...``).

Requests and responses follow the OpenAI format, so responses are returned as
plain dicts. NovelAI extensions (``min_p``, ``top_k``, ``unified_*``,
``generation_prefix``, ``enable_thinking``...) are regular fields; unknown
fields pass through unchanged.
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any, ClassVar

import curl_cffi
from curl_cffi.requests import AsyncSession
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ..._exceptions import SessionHttpError
from ...credential import CredentialBase
from ..schema import ApiBaseModel, close_stream, observed_session

logger = logging.getLogger(__name__)

_TEXT_ENDPOINT = "https://text.novelai.net"


class OAIChatMessage(BaseModel):
    role: str = Field(..., description='"system", "user" or "assistant"')
    content: str
    name: str | None = None


class _OAIGenerateBase(ApiBaseModel):
    _legacy_400_as_auth: ClassVar[bool] = False
    model: str
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: str | list[str] | None = None
    seed: int | None = None
    n: int | None = None
    # "stream" is set by the method: request() sends false, stream() sends true
    model_config = ConfigDict(extra="allow")
    _endpoint: str = PrivateAttr(_TEXT_ENDPOINT)

    def _body(self, stream: bool) -> dict:
        body = self.model_dump(mode="json", exclude_none=True)
        body["stream"] = stream
        return body

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> dict[str, Any]:
        """Non-streaming call; returns the OpenAI-format response."""
        response = await self._send(session, "POST", json_body=self._body(False), override_headers=override_headers)
        return response.json()

    async def stream(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Streaming call (server-sent events); yields each OpenAI-format chunk until ``[DONE]``."""
        body = self._body(True)
        async with observed_session(session, self.base_url, self.model) as (sess, observed):
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            try:
                response = await observed.send(sess, "POST", self.base_url, json=body, stream=True)
                try:
                    if response.status_code >= 400:
                        self._raise_for_status(
                            response.status_code, await response.acontent(), body, self._legacy_400_as_auth
                        )
                    async for line in response.aiter_lines():
                        text = line.decode("utf-8") if isinstance(line, bytes) else line
                        if not text.startswith("data:"):
                            continue
                        data = text[len("data:") :].strip()
                        if data == "[DONE]":
                            return
                        yield json.loads(data)
                finally:
                    await close_stream(response)
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.") from exc


class OAIChatCompletion(_OAIGenerateBase):
    """POST /oa/v1/chat/completions"""

    messages: list[OAIChatMessage]
    enable_thinking: bool | None = None

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/oa/v1/chat/completions"


class OAICompletion(_OAIGenerateBase):
    """POST /oa/v1/completions"""

    prompt: str | list[str]

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/oa/v1/completions"


class OAITokenCountResp(BaseModel):
    encoded: list[int] = Field(default_factory=list)
    length: int = 0


class OAITokenCount(ApiBaseModel):
    """POST /oa/v1/internal/token-count: tokenize a prompt with the model's tokenizer."""

    _legacy_400_as_auth: ClassVar[bool] = False

    model: str
    prompt: str | list[str]
    model_config = ConfigDict(extra="allow")
    _endpoint: str = PrivateAttr(_TEXT_ENDPOINT)

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/oa/v1/internal/token-count"

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> OAITokenCountResp:
        body = self.model_dump(mode="json", exclude_none=True)
        response = await self._send(session, "POST", json_body=body, override_headers=override_headers)
        return OAITokenCountResp.model_validate_json(response.content)


class OAIModel(BaseModel):
    id: str
    object: str | None = None
    created: int | None = None
    owned_by: str | None = None


class OAIModelsResp(BaseModel):
    data: list[OAIModel] = Field(default_factory=list)
    object: str | None = None


class OAIModels(ApiBaseModel):
    """GET /oa/v1/models: models available to this account."""

    _legacy_400_as_auth: ClassVar[bool] = False

    _endpoint: str = PrivateAttr(_TEXT_ENDPOINT)

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/oa/v1/models"

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> OAIModelsResp:
        response = await self._send(session, "GET", override_headers=override_headers)
        return OAIModelsResp.model_validate_json(response.content)
