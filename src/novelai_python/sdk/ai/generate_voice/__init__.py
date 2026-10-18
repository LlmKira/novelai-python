# @Author  : sudoskys
import logging
from enum import Enum
from typing import Literal, Union

import curl_cffi
import pydantic
from curl_cffi.requests import AsyncSession
from pydantic import ConfigDict, Field, PrivateAttr, model_validator

from novelai_python._retry import retry_on_server_error

from ...._exceptions import APIError, SessionHttpError
from ...._response.ai.generate_voice import VoiceResponse
from ....credential import CredentialBase
from ...schema import ApiBaseModel, use_session
from ._enum import Speaker, VoiceSpeakerV1, VoiceSpeakerV2

logger = logging.getLogger(__name__)


class VoiceGenerate(ApiBaseModel):
    """
    Voice Generate for /ai/generate-voice
    """

    _endpoint: str = PrivateAttr("https://api.novelai.net")
    text: str = Field(..., description="Text to generate voice", max_length=1000)
    """Limit 1000 characters"""
    voice: int = Field(default=-1, description="Seed", ge=-1)
    """Voice engine sid"""
    seed: str | None = Field(default=None, description="seed_seed", max_length=50)
    """
    Starting with a common first name will have a relevant influence on pitch and intonation. 
    The voice for any given seed is liable to change in the future as we continue to develop the TTS.
    """
    opus: bool = False
    version: Literal["v2", "v1"] | str = "v2"

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_model(self):
        # Validate seed
        if self.voice == -1 and self.seed is None:
            raise pydantic.ValidationError("Seed must be set when voice is -1")
        return self

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/generate-voice"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        self._endpoint = value

    @classmethod
    def build(
        cls, text: str, speaker: VoiceSpeakerV2 | VoiceSpeakerV1 | Speaker | str, *, opus: bool = True
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
            return cls(text=text, voice=-1, seed=speaker, opus=opus, version="v2")
        return cls(text=text, seed=speaker.seed, voice=speaker.sid, opus=opus, version=speaker.version)

    @retry_on_server_error()
    async def request(
        self, session: Union[AsyncSession, "CredentialBase"], *, override_headers: dict | None = None
    ) -> VoiceResponse:
        """
        生成图片
        :param override_headers:
        :param session:  session
        :return: VoiceResponse
        """
        # Data Build
        request_data = self.model_dump(mode="json", exclude_none=True)
        async with use_session(session) as sess:
            # Header
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            # Log
            logger.debug(f"Voice request data: {request_data}")
            # Request
            try:
                response = await sess.post(url=self.base_url, json=request_data)
                header_type = response.headers.get("Content-Type")
                if (
                    header_type not in ["audio/mpeg", "audio/ogg", "audio/opus", "audio/wav", "audio/webm"]
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
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, maybe SSL error. Try again later!"
                ) from exc
            except APIError:
                raise  # not an unexpected error: keep it out of the handler below
            except Exception as e:
                logger.exception("An Unexpected error occurred")
                raise e
