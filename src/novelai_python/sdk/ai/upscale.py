# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 上午10:48
# @Author  : sudoskys
# @File    : upscale.py
# @Software: PyCharm
import base64
import json
from io import BytesIO
from typing import Optional, Union
from urllib.parse import urlparse
from zipfile import ZipFile

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import ConfigDict, PrivateAttr, model_validator
from tenacity import wait_random, retry, stop_after_attempt, retry_if_exception

from ..schema import ApiBaseModel
from ..._exceptions import APIError, AuthError, SessionHttpError
from ..._response.ai.upscale import UpscaleResp
from ...credential import CredentialBase
from ...utils import try_jsonfy, NovelAiMetadata


class Upscale(ApiBaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")
    image: Union[str, bytes]  # base64
    width: Optional[int] = None
    height: Optional[int] = None
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
                raise ValueError("Invalid image size and cant auto detect, must be set width and height.")
        else:
            if self.width is None:
                self.width = width
            if self.height is None:
                self.height = height
        return self

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/upscale"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    async def necessary_headers(self, request_data) -> dict:
        """
        :param request_data:
        :return:
        """
        return {
            "Host": urlparse(self.endpoint).netloc,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://novelai.net/",
            "Content-Type": "application/json",
            "Origin": "https://novelai.net",
            "Content-Length": str(len(json.dumps(request_data).encode("utf-8"))),
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    @retry(
        wait=wait_random(min=1, max=3),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(lambda e: hasattr(e, "code") and str(e.code) == "500"),
        reraise=True
    )
    async def request(self,
                      session: Union[AsyncSession, "CredentialBase"],
                      *,
                      override_headers: Optional[dict] = None,
                      remove_sign: bool = False
                      ) -> UpscaleResp:
        """
        生成图片
        :param override_headers:
        :param session:  session
        :param remove_sign:  移除追踪信息
        :return:
        """
        # Data Build
        request_data = self.model_dump(mode="json", exclude_none=True)
        # Header
        if isinstance(session, AsyncSession):
            session.headers.update(await self.necessary_headers(request_data))
        elif isinstance(session, CredentialBase):
            update_header = await self.necessary_headers(request_data)
            session = await session.get_session(update_headers=update_header)
        if override_headers:
            session.headers.clear()
            session.headers.update(override_headers)
        try:
            _log_data = request_data.copy()
            _log_data.update({"image": "base64 data"}) if isinstance(_log_data.get("image"), str) else None
            logger.info(f"Upscale request data: {_log_data}")
        except Exception as e:
            logger.warning(f"Error when print log data: {e}")
        try:
            assert hasattr(session, "post"), "session must have post method."
            response = await session.post(
                self.base_url,
                data=json.dumps(request_data).encode("utf-8")
            )
            if response.headers.get('Content-Type') not in ['binary/octet-stream', 'application/x-zip-compressed']:
                logger.error(
                    f"Error with content type: {response.headers.get('Content-Type')} and code: {response.status_code}"
                )
                try:
                    _msg = response.json()
                except Exception as e:
                    logger.warning(e)
                    if not isinstance(response.content, str) and len(response.content) < 50:
                        raise APIError(
                            message=f"Unexpected content type: {response.headers.get('Content-Type')}",
                            request=request_data,
                            code=response.status_code,
                            response=try_jsonfy(response.content)
                        )
                    else:
                        _msg = {"statusCode": response.status_code, "message": response.content}
                status_code = _msg.get("statusCode", response.status_code)
                message = _msg.get("message", "Unknown error")
                if status_code in [400, 401, 402]:
                    # 400 : validation error
                    # 401 : unauthorized
                    # 402 : payment required
                    # 409 : conflict
                    raise AuthError(message, request=request_data, code=status_code, response=_msg)
                if status_code in [409]:
                    # conflict error
                    raise APIError(message, request=request_data, code=status_code, response=_msg)
                """
                if status_code in [429]:
                    # concurrent error
                    raise ConcurrentGenerationError(
                        message=message,
                        request=request_data,
                        code=status_code,
                        response=_msg
                    )
                """
                raise APIError(message, request=request_data, code=status_code, response=_msg)
            zip_file = ZipFile(BytesIO(response.content))
            unzip_content = []
            with zip_file as zf:
                file_list = zf.namelist()
                if not file_list:
                    raise APIError(
                        message="No file in zip",
                        request=request_data,
                        code=response.status_code,
                        response=try_jsonfy(response.content)
                    )
                for filename in file_list:
                    data = zip_file.read(filename)
                    if remove_sign:
                        try:
                            data = NovelAiMetadata.rehash(BytesIO(data), remove_stealth=True)
                            if not isinstance(data, bytes):
                                data = data.getvalue()
                        except Exception as e:
                            logger.exception(f"SdkWarn:Remove sign error: {e}")
                    unzip_content.append((filename, data))
            return UpscaleResp(
                meta=UpscaleResp.RequestParams(
                    endpoint=self.base_url,
                    raw_request=request_data,
                ),
                files=unzip_content[0]
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
