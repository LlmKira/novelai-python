# @Time    : 2024/2/13 上午10:48
# @Author  : sudoskys
# @File    : upscale.py
import base64
import json
import logging
from io import BytesIO
from typing import Union
from zipfile import BadZipFile, ZipFile

import curl_cffi
from curl_cffi.requests import AsyncSession
from pydantic import ConfigDict, PrivateAttr, model_validator

from novelai_python._retry import retry_on_server_error

from ..._exceptions import DataSerializationError, SessionHttpError
from ..._response.ai.upscale import UpscaleResp
from ...credential import CredentialBase
from ...metrics import get_metrics
from ...utils import try_jsonfy
from ..schema import ApiBaseModel, use_session

logger = logging.getLogger(__name__)

PNG_SIGNATURE = bytes([0x89]) + b"PNG"


class Upscale(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    image: str | bytes  # base64
    width: int | None = None
    height: int | None = None
    scale: float = 4
    """Kept for compatibility; the API upscales x4 and no longer takes it."""
    model: str = "nai-diffusion-5-full"
    """The model selected in the web client; the API rejects the request without it."""
    declared_blur_sigma: float = 0
    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_model(self):
        if isinstance(self.image, str) and self.image.startswith("data:image/"):
            raise ValueError("Invalid image format, must be base64 encoded.")
        if isinstance(self.image, bytes):
            self.image = base64.b64encode(self.image).decode("utf-8")
        # Auto detect image size
        try:
            from PIL import Image

            with Image.open(BytesIO(base64.b64decode(self.image))) as img:
                width, height = img.size
        except Exception as e:
            logger.warning(f"Error when validate image size: {e}")
            if self.width is None or self.height is None:
                raise ValueError("Invalid image size and cant auto detect, must be set width and height.") from e
        else:
            if self.width is None:
                self.width = width
            if self.height is None:
                self.height = height
        return self

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/upscale"

    @retry_on_server_error()
    async def request(
        self, session: Union[AsyncSession, "CredentialBase"], *, override_headers: dict | None = None
    ) -> UpscaleResp:
        """
        Upscale an image (x4). Sent the way the web client does: multipart with the PNG as
        part ``image`` and ``{"image": "image", "model": ..., "declared_blur_sigma": ...}`` as ``request``.
        :raises AuthError: 400 / 401 / 402 (402: not enough Anlas).
        :raises APIError: any other error status.
        :raises DataSerializationError: the response holds no image.
        """
        from .generate_image import build_multipart_request

        request_data = {"image": "image", "model": self.model, "declared_blur_sigma": self.declared_blur_sigma}
        body, content_type = build_multipart_request(
            json.dumps(request_data).encode("utf-8"), [("image", base64.b64decode(self.image))]
        )
        async with get_metrics().observe(self.base_url, self.model) as observed, use_session(session) as sess:
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            logger.debug(f"Request Data: {request_data}")
            try:
                response = await sess.post(self.base_url, data=body, headers={"Content-Type": content_type})
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.") from exc
            observed.report(response.status_code)
        if response.status_code >= 400:
            self._raise_for_status(response.status_code, response.content, request_data)
        content = response.content
        try:
            with ZipFile(BytesIO(content)) as zf:
                files = [(name, zf.read(name)) for name in zf.namelist()]
        except BadZipFile:
            # a bare image instead of a ZIP
            ext = "webp" if content[:4] == b"RIFF" else "png"
            files = [(f"image_0.{ext}", content)] if content[:4] in (b"RIFF", PNG_SIGNATURE) else []
        if not files:
            raise DataSerializationError(
                message="The upscale response holds no image.",
                request=request_data,
                response=try_jsonfy(content[:200]),
                code=response.status_code,
            )
        return UpscaleResp(
            meta=UpscaleResp.RequestParams(endpoint=self.base_url, raw_request=request_data),
            files=files[0],
        )
