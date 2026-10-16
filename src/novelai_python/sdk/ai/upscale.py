# @Time    : 2024/2/13 上午10:48
# @Author  : sudoskys
# @File    : upscale.py
import base64
import json
import logging
from copy import deepcopy
from io import BytesIO
from typing import Union
from zipfile import BadZipFile, ZipFile

import curl_cffi
from curl_cffi.requests import AsyncSession
from pydantic import ConfigDict, PrivateAttr, model_validator

from novelai_python._retry import retry_on_server_error

from ..._exceptions import APIError, AuthError, DataSerializationError, SessionHttpError
from ..._response.ai.upscale import UpscaleResp
from ...credential import CredentialBase
from ...utils import try_jsonfy
from ..schema import ApiBaseModel

logger = logging.getLogger(__name__)


class Upscale(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    image: str | bytes  # base64
    width: int | None = None
    height: int | None = None
    scale: float = 4
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

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        self._endpoint = value

    @retry_on_server_error()
    async def request(
        self, session: Union[AsyncSession, "CredentialBase"], *, override_headers: dict | None = None
    ) -> UpscaleResp:
        """
        生成图片
        :param override_headers:
        :param session:  session
        :return:
        """
        # Prepare request data
        request_data = self.model_dump(mode="json", exclude_none=True)
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)

            # Log the request data (sanitize sensitive content)
            try:
                log_data = deepcopy(request_data)
                if self.image:
                    log_data["image"] = "base64 data hidden"
                logger.debug(f"Request Data: {json.dumps(log_data, indent=2)}")
            except Exception as e:
                logger.warning(f"Failed to log request data: {e}")

            # Perform request and handle response
            try:
                self.ensure_session_has_post_method(sess)
                response = await sess.post(self.base_url, data=json.dumps(request_data).encode("utf-8"))
                if (
                    response.headers.get("Content-Type") not in ["binary/octet-stream", "application/x-zip-compressed"]
                    or response.status_code >= 400
                ):
                    error_message = await self.handle_error_response(response=response, request_data=request_data)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400, 401, 402]:
                        # 400 : validation error
                        # 401 : unauthorized
                        # 402 : payment required
                        # 409 : conflict
                        raise AuthError(message, request=request_data, code=status_code, response=error_message)
                    if status_code in [409]:
                        # conflict error
                        raise APIError(message, request=request_data, code=status_code, response=error_message)
                    raise APIError(message, request=request_data, code=status_code, response=error_message)

                # Unpack the ZIP response
                try:
                    zip_file = ZipFile(BytesIO(response.content))
                    unzip_content = []
                    with zip_file as zf:
                        file_list = zf.namelist()
                        if not file_list:
                            raise DataSerializationError(
                                message="The ZIP response contains no files.",
                                request=request_data,
                                response=try_jsonfy(response.content),
                                code=response.status_code,
                            )
                        for filename in file_list:
                            data = zip_file.read(filename)
                            unzip_content.append((filename, data))
                    return UpscaleResp(
                        meta=UpscaleResp.RequestParams(
                            endpoint=self.base_url,
                            raw_request=request_data,
                        ),
                        files=unzip_content[0],
                    )
                except BadZipFile as e:
                    # Invalid ZIP file - indicate serialization error
                    logger.exception("The response content is not a valid ZIP file.")
                    raise DataSerializationError(
                        message="Invalid ZIP file received from the API.",
                        request=request_data,
                        response={},
                        code=response.status_code,
                    ) from e
                except Exception as e:
                    logger.exception("Unexpected error while unpacking ZIP response.")
                    raise DataSerializationError(
                        message="An unexpected error occurred while processing ZIP data.",
                        request=request_data,
                        response={},
                        code=response.status_code,
                    ) from e
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, maybe SSL error. Try again later!"
                ) from exc
            except APIError as e:
                raise e
            except Exception as e:
                logger.exception("An Unexpected error occurred")
                raise e
