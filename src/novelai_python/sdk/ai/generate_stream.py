# @Author  : sudoskys
import logging
from collections.abc import AsyncIterable
from typing import Union

import curl_cffi
from curl_cffi.requests import AsyncSession

from ..._enum import TextLLMModelTypeAlias
from ..._exceptions import APIError, SessionHttpError
from ..._response.ai.generate_stream import LLMStreamResp
from ...credential import CredentialBase
from ...metrics import get_metrics
from ...utils import try_jsonfy
from ..schema import close_stream, use_session
from .generate import LLM, AdvanceLLMSetting, LLMGenerationParams, PenStyle, TextLLMModel

logger = logging.getLogger(__name__)


class LLMStream(LLM):
    """
    LLM Stream for /ai/generate-stream
    """

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/generate-stream"

    @classmethod
    def build(
        cls,
        prompt: str,
        model: TextLLMModelTypeAlias = TextLLMModel.ERATO,
        phrase_rep_pen: PenStyle = PenStyle.Off,
        *,
        advanced_setting: AdvanceLLMSetting = AdvanceLLMSetting(),
        parameters: LLMGenerationParams | None = None,
        default_bias: bool | None = True,
        logprobs_count: int | None = 10,
        bias_dinkus_asterism: bool | None = False,
        prefix: str | None = "vanilla",
        **kwargs,
    ) -> "LLMStream":
        """
        Generate Prompt
        """
        assert isinstance(prompt, str), "Prompt must be a string"
        created = cls(
            input=prompt,
            model=model,
            advanced_setting=advanced_setting,
            parameters=parameters,
            default_bias=default_bias,
            logprobs_count=logprobs_count,
            bias_dinkus_asterism=bias_dinkus_asterism,
            prefix=prefix,
        )
        return created

    # streams instead of returning one LLMResp
    async def request(  # pyright: ignore[reportIncompatibleMethodOverride]  # ty: ignore[invalid-method-override]
        self, session: Union[AsyncSession, "CredentialBase"], *, override_headers: dict | None = None
    ) -> AsyncIterable[LLMStreamResp]:
        """
        生成图片
        :param override_headers:
        :param session:  session
        :return: LLMStreamResp
        """
        # Data Build
        if self.parameters is None:
            raise ValueError("parameters are not set")
        base_map = self.parameters.get_base_map()
        parameters = {
            **base_map,
            **self.advanced_setting.model_dump(mode="json", exclude_none=True),
        }
        parameters.update(self.parameters.model_dump(mode="json", exclude_none=True).items())
        # Override
        request_data = {
            **self.model_dump(mode="json", include={"input", "model"}),
            "parameters": parameters,
        }
        async with get_metrics().observe(self.base_url, self.model) as observed, use_session(session) as sess:
            # Header
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            # Log
            logger.debug(f"StreamLLM request data: {request_data}")
            # Request
            try:
                response = await sess.post(
                    self.base_url,
                    json=request_data,
                    stream=True,  # 使用 stream=True 参数
                )
                (observed.ok if response.status_code < 400 else observed.failed)(response.status_code)
                try:
                    media_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                    is_event_stream = media_type == "text/event-stream"
                    if not is_event_stream:
                        # a stream=True response has no .content yet; the error body has to be read
                        response_data = try_jsonfy(await response.acontent(), default_when_error={})
                        if not isinstance(response_data, dict):
                            response_data = {}
                    else:
                        response_data = {}
                    message = (
                        response_data.get("error")
                        or response_data.get("message")
                        or f"Server error with status_code {response.status_code}"
                    )
                    status_code = response_data.get("statusCode", response.status_code)
                    if not is_event_stream:
                        if status_code == 400:
                            raise APIError(
                                "A validation error occured.", request=request_data, code=status_code, response=message
                            )
                        elif status_code == 401:
                            raise APIError(
                                "Access Token is incorrect.", request=request_data, code=status_code, response=message
                            )
                        elif status_code == 402:
                            raise APIError(
                                "An active subscription is required to access this endpoint.",
                                request=request_data,
                                code=status_code,
                                response=message,
                            )
                        elif status_code == 409:
                            raise APIError(
                                "A conflict error occured.", request=request_data, code=status_code, response=message
                            )
                        else:
                            raise APIError(
                                f"Server did not send text/event-stream, status code {status_code}",
                                request=request_data,
                                code=status_code,
                                response=message,
                            )
                    if response.status_code not in [200, 201]:
                        raise APIError(
                            f"Server error with status code {response.status_code}",
                            request=request_data,
                            code=response.status_code,
                            response=message,
                        )
                    # Streaming data processing
                    async for line in response.aiter_lines():
                        event = line.decode().strip().split(":", 1)
                        if len(event) == 2:
                            event_type, content = event
                            if event_type == "data":
                                llm_stream_resp = LLMStreamResp.model_validate_json(content)
                                llm_stream_resp.text = LLMStreamResp.decode(llm_stream_resp.token, self.model)
                                yield llm_stream_resp
                                if llm_stream_resp.final:  # Stop returning when final is True
                                    break
                finally:
                    await close_stream(response)
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, perhaps it's an SSL error. Please try again later!"
                ) from exc
            except APIError:
                raise  # not an unexpected error: keep it out of the handler below
            except Exception as e:
                logger.exception("An unexpected error occurred")
                raise e
