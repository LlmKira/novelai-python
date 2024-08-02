# -*- coding: utf-8 -*-
# @Author  : sudoskys
from typing import Optional, Union, Literal
from urllib.parse import urlparse

import curl_cffi
import httpx
import pydantic
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import ConfigDict, PrivateAttr, Field, model_validator
from tenacity import wait_random, retry, stop_after_attempt, retry_if_exception

from ._enum import VoiceSpeakerV1, VoiceSpeakerV2
from ...schema import ApiBaseModel
from ...._exceptions import APIError, SessionHttpError
from ...._response.ai.generate_voice import VoiceResponse
from ....credential import CredentialBase


class VoiceGenerate(ApiBaseModel):
    """
    Voice Generate for /ai/generate-voice
    """
    _endpoint: str = PrivateAttr("https://api.novelai.net")
    text: str = Field(..., description="Text to generate voice", max_length=1000)
    """Limit 1000 characters"""
    voice: int = Field(default=-1, description="Seed", ge=-1)
    """Voice engine sid"""
    seed: Optional[str] = Field(None, description="seed_seed", max_length=50)
    """
    Starting with a common first name will have a relevant influence on pitch and intonation. 
    The voice for any given seed is liable to change in the future as we continue to develop the TTS.
    """
    opus: bool = False
    version: Union[Literal["v2", "v1"], str] = "v2"

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_model(self):
        # Validate seed
        if self.voice == -1 and self.seed is None:
            raise pydantic.ValidationError("Seed must be set when voice is -1")
        return self

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate-voice"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    async def necessary_headers(self, request_data) -> dict:
        """
        :param request_data: dict
        :return: dict
        "Sec-Ch-Ua": '"Edge";v="123", "Not:A-Brand";v="8"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        """
        return {
            "Host": urlparse(self.endpoint).netloc,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Origin": "https://novelai.net",
            "Pragma": "no-cache",
            "Referer": "https://novelai.net/",
        }

    @classmethod
    def build(cls,
              text: str,
              voice_engine: Union[VoiceSpeakerV1, VoiceSpeakerV2, str],
              *,
              opus: bool = False
              ) -> "VoiceGenerate":
        """
        生成图片
        :param opus: unknown
        :param text: str
        :param voice_engine: VoiceSpeakerV1 or VoiceSpeakerV2 or str
        :return: VoiceGenerate instance
        :raises: ValueError
        """
        if isinstance(voice_engine, str):
            return cls(
                text=text,
                voice=-1,
                seed=voice_engine,
                opus=opus,
                version="v2"
            )
        if isinstance(voice_engine, VoiceSpeakerV2):
            return cls(
                text=text,
                seed=voice_engine.value.seed,
                voice=voice_engine.value.sid,
                opus=opus,
                version="v2"
            )
        if isinstance(voice_engine, VoiceSpeakerV1):
            return cls(
                text=text,
                seed=voice_engine.value.seed,
                voice=voice_engine.value.sid,
                opus=opus,
                version="v1"
            )
        raise ValueError("Invalid voice engine")

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
                      ) -> VoiceResponse:
        """
        生成图片
        :param override_headers:
        :param session:  session
        :return: VoiceResponse
        """
        # Data Build
        request_data = self.model_dump(mode="json", exclude_none=True)
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            # Header
            sess.headers.update(await self.necessary_headers(request_data))
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            # Log
            logger.debug(f"Voice request data: {request_data}")
            # Request
            try:
                assert hasattr(sess, "get"), "session must have get method."
                response = await sess.get(
                    self.base_url,
                    params=request_data
                )
                header_type = response.headers.get('Content-Type')
                if header_type not in ['audio/mpeg', 'audio/ogg', 'audio/opus']:
                    logger.warning(
                        f"Error with content type: {header_type} and code: {response.status_code}"
                    )
                    try:
                        _msg = response.json()
                    except Exception as e:
                        logger.warning(e)
                        if not isinstance(response.content, str) and len(response.content) < 50:
                            raise APIError(
                                message=f"Unexpected content: {header_type} with code: {response.status_code}",
                                request=request_data,
                                code=response.status_code,
                                response="UnJsoned content"
                            )
                        else:
                            _msg = {"statusCode": response.status_code, "message": response.content}
                    status_code = _msg.get("statusCode", response.status_code)
                    message = _msg.get("message", "Unknown error")
                    if status_code in [400]:
                        # Validation tts version error
                        raise APIError(message, request=request_data, code=status_code, response=_msg)
                    raise APIError(message, request=request_data, code=status_code, response=_msg)
                return VoiceResponse(
                    meta=request_data,
                    audio=response.content,
                )
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
