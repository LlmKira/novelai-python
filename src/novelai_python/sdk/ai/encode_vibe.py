# @File    : encode_vibe.py

import base64
from typing import ClassVar

from curl_cffi.requests import AsyncSession
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

from novelai_python._retry import retry_on_server_error

from ...credential import CredentialBase
from ..schema import ApiBaseModel
from ._enum import Model, ModelTypeAlias, get_supported_params


class EncodeVibeResp(BaseModel):
    vibe: bytes = Field(..., description="Encoded vibe, binary")

    @property
    def vibe_b64(self) -> str:
        """The form ``reference_image_multiple`` takes: pass it instead of an image to skip re-encoding."""
        return base64.b64encode(self.vibe).decode("utf-8")


class EncodeVibe(ApiBaseModel):
    """POST /ai/encode-vibe: encode an image once for vibe transfer.

    Only models with ``encodedVibes`` (V4 / V4.5) take vibes; V5 has no vibe transfer.
    The web client sends only ``image``, ``information_extracted``, ``mask`` and ``model``.
    """

    _auth_on_400: ClassVar[bool] = False

    image: str | bytes
    model: ModelTypeAlias = Model.NAI_DIFFUSION_4_5_FULL
    information_extracted: float = Field(default=1.0, ge=0, le=1)
    mask: str | bytes | None = None
    crop_to_mask: bool | None = None
    focus_seed: int | None = None
    info_extract_seed: int | None = None
    model_config = ConfigDict(extra="ignore")
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    @field_validator("image", "mask")
    @classmethod
    def _to_b64(cls, v: str | bytes | None) -> str | None:
        if isinstance(v, bytes):
            return base64.b64encode(v).decode("utf-8")
        if isinstance(v, str) and v.startswith("data:"):
            raise ValueError("Pass raw base64 or bytes, not a data: URL.")
        return v

    @model_validator(mode="after")
    def _check_model(self):
        if not get_supported_params(self.model).encodedVibes:
            raise ValueError(f"{self.model} does not take encoded vibes (V4 / V4.5 only)")
        return self

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/encode-vibe"

    @retry_on_server_error()
    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> EncodeVibeResp:
        body = self.model_dump(mode="json", exclude_none=True)
        response = await self._send(session, "POST", json_body=body, override_headers=override_headers)
        return EncodeVibeResp(vibe=response.content)
