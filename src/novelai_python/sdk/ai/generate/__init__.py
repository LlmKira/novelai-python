# -*- coding: utf-8 -*-
# @Author  : sudoskys
from typing import Optional, Union, List
from urllib.parse import urlparse

import curl_cffi
import httpx
import pydantic
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import ConfigDict, PrivateAttr, model_validator, Field
from tenacity import wait_random, retry, stop_after_attempt, retry_if_exception

from ._const import d_repetition_penalty_whitelist, d_bad_words_ids
from ._enum import TextLLMModel, PenStyle, generate_order, TOKENIZER
from ._preset import Params, PRESET
from ...schema import ApiBaseModel
from ...._exceptions import APIError, SessionHttpError
from ...._response.ai.generate import LLMResp
from ....credential import CredentialBase
from ....tokenizer import LLMTokenizer
from ....utils.encode import tokens_to_b64


class LLM(ApiBaseModel):
    """
    LLM for /ai/generate
    """
    _endpoint: str = PrivateAttr("https://api.novelai.net")
    input: str = Field(..., description="Base64 encoded token text")
    model: Union[TextLLMModel, str] = TextLLMModel.Kayra
    """Model to use"""
    parameters: Params = Params()

    model_config = ConfigDict(extra="ignore")

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate"

    async def necessary_headers(self, request_data) -> dict:
        """
        :param request_data: dict
        :return: dict
        """
        return {
            "Host": urlparse(self.endpoint).netloc,
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "Referer": "https://novelai.net/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

    @model_validator(mode="after")
    def validate_model(self):
        tokenizer = LLMTokenizer()
        if isinstance(self.input, str):
            prompt = tokenizer.encode(self.input, tokenizer_name=TOKENIZER.get(self.model))
            self.input = tokens_to_b64(prompt)
        if self.parameters.stop_sequences:
            if not isinstance(self.parameters.stop_sequences, list):
                raise pydantic.ValidationError("stop_sequences must be a list")
            stop_sequences = []
            for i, obj in enumerate(self.parameters.stop_sequences):
                if isinstance(obj, str):
                    stop_sequences.append(tokenizer.encode(obj, tokenizer_name=TOKENIZER.get(self.model)))
                elif not isinstance(obj, list):
                    raise ValueError(
                        f"Expected type 'str' or 'list' for item #{i} of 'stop_sequences', " f"but got '{type(obj)}'"
                    )
            self.parameters.stop_sequences = stop_sequences
        if self.parameters.repetition_penalty:
            # adjust repetition penalty value for Sigurd and Euterpe
            if self.model in (TextLLMModel.Sigurd, TextLLMModel.Euterpe):
                rep_pen = self.parameters.repetition_penalty
                self.parameters.repetition_penalty = (0.525 * (rep_pen - 1) / 7) + 1

        return self

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
              ) -> "LLM":
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
                      ) -> LLMResp:
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
            logger.debug(f"LLM request data: {request_data}")
            # Request
            try:
                assert hasattr(sess, "post"), "session must have post method."
                response = await sess.post(
                    self.base_url,
                    json=request_data,
                    stream=False
                )
                header_type = response.headers.get('Content-Type')
                if "application/json" not in header_type:
                    try:
                        _msg = response.json()
                    except Exception as e:
                        _msg = {"statusCode": response.status_code, "message": response.content}
                    status_code = _msg.get("statusCode", response.status_code)
                    message = _msg.get("message", "Unknown error")
                    if status_code == 400:
                        raise APIError(
                            f"A validation error occured. {message}",
                            request=request_data, code=status_code, response=_msg
                        )

                    elif status_code == 401:
                        raise APIError(
                            f"Access Token is incorrect. {message}",
                            request=request_data, code=status_code, response=_msg
                        )
                    elif status_code == 402:
                        raise APIError(
                            f"An active subscription is required to access this endpoint. {message}",
                            request=request_data, code=status_code, response=_msg
                        )
                    elif status_code == 409:
                        raise APIError(
                            f"A conflict error occured. {message}",
                            request=request_data, code=status_code, response=_msg
                        )
                    else:
                        raise APIError(
                            f"An unknown error occured. {response.status_code} {message}",
                            request=request_data, code=status_code, response=_msg
                        )
                else:
                    output = response.json().get("output", None)
                    assert output, APIError("No Content Returned",
                                            request=request_data, code=response.status_code, response=response.content
                                            )
                    return LLMResp(
                        output=output,
                        text=LLMResp.decode_token(model=self.model, token_str=output)
                    )
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, perhaps it's an SSL error. Please try again later!"
                )
            except httpx.HTTPError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An HTTPError occurred, perhaps it's an SSL error. Please try again later!"
                )
            except APIError as e:
                raise e
            except Exception as e:
                logger.opt(exception=e).exception("An unexpected error occurred")
                raise e
