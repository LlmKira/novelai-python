# -*- coding: utf-8 -*-
# @Author  : sudoskys
import json
from typing import Optional, Union, AsyncIterable

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from tenacity import wait_random, retry, stop_after_attempt, retry_if_exception

from .generate import LLM, TextLLMModel, PenStyle, AdvanceLLMSetting, LLMGenerationParams
from ..._enum import TextLLMModelTypeAlias
from ..._exceptions import APIError, SessionHttpError
from ..._response.ai.generate_stream import LLMStreamResp
from ...credential import CredentialBase
from ...utils import try_jsonfy


class LLMStream(LLM):
    """
    LLM Stream for /ai/generate-stream
    """

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate-stream"

    @classmethod
    def build(cls,
              prompt: str,
              model: TextLLMModelTypeAlias = TextLLMModel.ERATO,
              phrase_rep_pen: PenStyle = PenStyle.Off,
              *,
              advanced_setting: AdvanceLLMSetting = AdvanceLLMSetting(),
              parameters: Optional[LLMGenerationParams] = None,
              default_bias: Optional[bool] = True,
              logprobs_count: Optional[int] = 10,
              bias_dinkus_asterism: Optional[bool] = False,
              prefix: Optional[str] = "vanilla",
              **kwargs
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

    @retry(
        wait=wait_random(min=1, max=3),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(lambda e: hasattr(e, "code") and str(e.code) == "500"),
        reraise=True
    )
    async def request(self,
                      session: Union[AsyncSession, "CredentialBase"],
                      *,
                      override_headers: Optional[dict] = None
                      ) -> AsyncIterable[LLMStreamResp]:
        """
        生成图片
        :param override_headers:
        :param session:  session
        :return: LLMStreamResp
        """
        # Data Build
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
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            # Header
            sess.headers.update(await self.necessary_headers(request_data))
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            # Log
            logger.debug(f"StreamLLM request data: {request_data}")
            # Request
            try:
                assert hasattr(sess, "post"), "session must have post method."
                response = await sess.post(
                    self.base_url,
                    json=request_data,
                    stream=True  # 使用 stream=True 参数
                )
                response_data = try_jsonfy(response.content, default_when_error={})
                message = response_data.get("error") or response_data.get(
                    "message") or f"Server error with status_code {response.status_code}"
                status_code = response_data.get("statusCode", response.status_code)
                header_type = response.headers.get('Content-Type')
                # 检查 'Content-Type' 是否为 'text/event-stream'
                if header_type not in ['text/event-stream']:
                    if status_code == 400:
                        raise APIError(
                            "A validation error occured.",
                            request=request_data, code=status_code, response=message
                        )
                    elif status_code == 401:
                        raise APIError(
                            "Access Token is incorrect.",
                            request=request_data, code=status_code, response=message
                        )
                    elif status_code == 402:
                        raise APIError(
                            "An active subscription is required to access this endpoint.",
                            request=request_data, code=status_code, response=message
                        )
                    elif status_code == 409:
                        raise APIError(
                            "A conflict error occured.",
                            request=request_data, code=status_code, response=message
                        )
                    else:
                        raise APIError(
                            f"Server did not send text/event-stream, status code {status_code}",
                            request=request_data, code=status_code, response=message
                        )
                else:
                    if response.status_code not in [200, 201]:
                        raise APIError(
                            f"Server error with status code {response.status_code}",
                            request=request_data, code=response.status_code, response=response.content
                        )
                    # Streaming data processing
                    async for line in response.aiter_lines():
                        event = line.decode().strip().split(":", 1)
                        if len(event) == 2:
                            event_type, content = event
                            if event_type == 'data':
                                llm_stream_resp = LLMStreamResp.model_validate(json.loads(content))
                                llm_stream_resp.text = LLMStreamResp.decode(llm_stream_resp.token, self.model)
                                yield llm_stream_resp
                                if llm_stream_resp.final:  # Stop returning when final is True
                                    break
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, perhaps it's an SSL error. Please try again later!")
            except httpx.HTTPError as exc:
                logger.exception(exc)
                raise SessionHttpError("An HTTPError occurred, perhaps it's an SSL error. Please try again later!")
            except APIError as e:
                raise e
            except Exception as e:
                logger.opt(exception=e).exception("An unexpected error occurred")
                raise e
