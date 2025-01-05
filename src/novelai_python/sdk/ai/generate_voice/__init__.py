# -*- coding: utf-8 -*-
# @Author  : sudoskys
from enum import Enum
from typing import Optional, Union, Literal
from urllib.parse import urlparse

import curl_cffi
import httpx
import pydantic
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import ConfigDict, PrivateAttr, Field, model_validator
from tenacity import wait_random, retry, stop_after_attempt, retry_if_exception

from ._enum import VoiceSpeakerV1, VoiceSpeakerV2, Speaker
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
              speaker: Union[VoiceSpeakerV2, VoiceSpeakerV1, Speaker, str],
              *,
              opus: bool = True
              ) -> "VoiceGenerate":
        """
        生成图片
        :param opus: unknown
        :param text: str
        :param speaker: Speaker import from novelai_python.sdk.ai.generate_voice._enum
        :return: VoiceGenerate instance
        :raises: ValueError
        """
        if isinstance(speaker, Enum):
            speaker = speaker.value

        if isinstance(speaker, str):
            return cls(
                text=text,
                voice=-1,
                seed=speaker,
                opus=opus,
                version="v2"
            )
        return cls(
            text=text,
            seed=speaker.seed,
            voice=speaker.sid,
            opus=opus,
            version=speaker.version
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
                self.ensure_session_has_post_method(sess)
                response = await sess.post(
                    url=self.base_url,
                    json=request_data
                )
                header_type = response.headers.get('Content-Type')
                if (
                        header_type not in ['audio/mpeg', 'audio/ogg', 'audio/opus', 'audio/wav', 'audio/webm']
                        or response.status_code >= 400
                ):

                    error_message = await self.handle_error_response(response=response, request_data=request_data)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400]:
                        # Validation tts version error
                        raise APIError(message, request=request_data, code=status_code, response=error_message)
                    raise APIError(message, request=request_data, code=status_code, response=error_message)
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
