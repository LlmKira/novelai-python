# -*- coding: utf-8 -*-
# @Author  : sudoskys
import json
from typing import Optional, Union, List, AsyncIterable

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from tenacity import wait_random, retry, stop_after_attempt, retry_if_exception

from .generate import LLM, generate_order, TextLLMModel, PenStyle, PRESET
from .generate_image import Params
from ..._exceptions import APIError, SessionHttpError
from ..._response.ai.generate_stream import LLMStreamResp
from ...credential import CredentialBase


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
              model: TextLLMModel = TextLLMModel.Kayra,
              min_length: Optional[int] = None,
              max_length: Optional[int] = None,
              temperature: Optional[float] = None,
              top_k: Optional[int] = None,
              top_p: Optional[float] = None,
              frequency_penalty: Optional[float] = None,
              presence_penalty: Optional[float] = None,
              stop_sequences: Optional[Union[List[str]]] = None,
              repetition_penalty: Optional[float] = None,
              pen_style: Optional[PenStyle] = None,
              **kwargs
              ) -> "LLMStream":
        """
        Generate Prompt
        """
        assert isinstance(prompt, str), "Prompt must be a string"
        # 清理空值
        kwarg = {
            "min_length": min_length,
            "max_length": max_length,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stop_sequences": stop_sequences,
            "repetition_penalty": repetition_penalty,
            "pen_style": pen_style
        }
        kwargs = {**kwarg, **kwargs}
        param = {k: v for k, v in kwargs.items() if v is not None}
        _preset_model = PRESET.get(model.name, {})
        if not _preset_model:
            _build_prop = Params.model_validate(param)
        else:
            _build_prop = _preset_model.model_copy(deep=True, update=param)
        assert _build_prop is not None, "Params validate failed"
        return cls(
            input=prompt,
            model=model,
            parameters=_build_prop
        )

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
        request_data = self.model_dump(mode="json", exclude_none=True)
        request_data["order"] = generate_order(request_data) or []
        assert request_data.get("parameters"), "Parameters is required"
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
                header_type = response.headers.get('Content-Type')
                # 检查 'Content-Type' 是否为 'text/event-stream'
                if header_type not in ['text/event-stream']:
                    try:
                        _msg = response.json()
                    except Exception as e:
                        _msg = {"statusCode": response.status_code, "message": response.content}
                    status_code = _msg.get("statusCode", response.status_code)
                    message = _msg.get("message", "Unknown error")
                    if status_code == 400:
                        raise APIError(
                            "A validation error occured.",
                            request=request_data, code=status_code, response=_msg
                        )

                    elif status_code == 401:
                        raise APIError(
                            "Access Token is incorrect.",
                            request=request_data, code=status_code, response=_msg
                        )
                    elif status_code == 402:
                        raise APIError(
                            "An active subscription is required to access this endpoint.",
                            request=request_data, code=status_code, response=_msg
                        )
                    elif status_code == 409:
                        raise APIError(
                            "A conflict error occured.",
                            request=request_data, code=status_code, response=_msg
                        )
                    else:
                        raise APIError(
                            "An unknown error occured.",
                            request=request_data, code=status_code, response=_msg
                        )
                else:
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
