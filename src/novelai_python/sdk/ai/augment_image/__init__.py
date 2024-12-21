# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:08
# @Author  : sudoskys
# @File    : __init__.py.py

import base64
import io
import json
import pathlib
from copy import deepcopy
from io import BytesIO
from typing import Optional, Union, IO, Any
from urllib.parse import urlparse
from zipfile import ZipFile

import curl_cffi
import httpx
from PIL import Image
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import ConfigDict, PrivateAttr, model_validator, Field
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception

from novelai_python.sdk.ai._cost import CostCalculator
from novelai_python.sdk.ai._enum import Model
from ._enum import ReqType, Moods
from ...schema import ApiBaseModel
from ...._exceptions import APIError, AuthError, ConcurrentGenerationError, SessionHttpError
from ...._response.ai.generate_image import ImageGenerateResp, RequestParams
from ....credential import CredentialBase
from ....utils import try_jsonfy


class AugmentImageInfer(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    req_type: ReqType = Field(..., description="Type of augmentation")
    width: int = Field(..., description="Width of the image")
    height: int = Field(..., description="Height of the image")
    image: Union[str, bytes] = Field(..., description="Base64 encoded image")
    prompt: Optional[str] = None
    """For mood based generation, prompt should be in the format of `mood;;prompt`"""
    defry: Optional[int] = Field(0, ge=0, le=5, multiple_of=1)
    """The larger the value, the weaker the defry effect"""
    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def image_validator(self):
        if isinstance(self.image, bytes):
            self.image = base64.b64encode(self.image).decode("utf-8")
        if isinstance(self.image, str) and self.image.startswith("data:"):
            raise ValueError("Invalid `image` format, must be base64 encoded directly.")
        if isinstance(self.image, str) and self.image.startswith("+vv"):
            raise ValueError("Invalid `image` format, must be encoded correctly.")
        if self.prompt and self.req_type == ReqType.EMOTION:
            valid_starts = [enum.value for enum in Moods]
            if not any(self.prompt.startswith(f"{valid_start};;") for valid_start in valid_starts):
                raise ValueError(f"Invalid `prompt` format, must start with one of {valid_starts}.")
        return self

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/augment-image"

    def calculate_cost(self, is_opus: bool = False) -> float:
        """
        Calculate the cost of the request
        :param is_opus: Whether the user is a VIP3 user
        :return: The cost of the request
        :raises NotImplementedError: When the request type is BG_REMOVAL
        """
        # NOTE: its unclear how the cost is calculated
        try:
            if self.req_type == ReqType.BG_REMOVAL:
                return CostCalculator.calculate(
                    width=self.width,
                    height=self.height,
                    steps=28,
                    model=Model.NAI_DIFFUSION_3,
                    image=bool(self.image),
                    n_samples=1,
                    account_tier=1,
                    strength=1,
                    sampler=None,
                    is_sm_enabled=False,
                    is_sm_dynamic=False,
                    is_account_active=True,
                    tool=self.req_type.value,
                ) * 3 + 5
            return CostCalculator.calculate(
                width=self.width,
                height=self.height,
                steps=28,
                model=Model.NAI_DIFFUSION_3,
                image=bool(self.image),
                n_samples=1,
                account_tier=3 if is_opus else 1,
                strength=1,
                sampler=None,
                is_sm_enabled=False,
                is_sm_dynamic=False,
                is_account_active=True,
                tool=self.req_type.value,
            )
        except Exception as e:
            raise ValueError(f"Error when calculating cost") from e

    @staticmethod
    def _to_bytes_io(image: Union[bytes, IO, pathlib.Path, Any]) -> io.BytesIO:
        """
        将输入图像转换为 BytesIO 对象。

        :param image: 可以是 bytes、IO、pathlib.Path 或任何拥有 read() 方法的对象
        :return: BytesIO 对象
        :raises ValueError: 输入类型无效时抛出
        """
        if isinstance(image, bytes):
            return io.BytesIO(image)
        elif isinstance(image, pathlib.Path):
            with open(image, 'rb') as f:
                return io.BytesIO(f.read())
        elif hasattr(image, 'read') and callable(image.read):
            return io.BytesIO(image.read())
        else:
            raise ValueError("Invalid image input type. Expected bytes, IO, pathlib.Path, or any readable object.")

    @classmethod
    def build(cls,
              image: Union[bytes, IO, pathlib.Path],
              req_type: ReqType = ReqType.SKETCH,
              *,
              defry: Optional[int] = None,
              prompt: Optional[str] = None,
              mood: Optional[Moods] = None,
              ):
        """
        Build the request data
        :param req_type: Request type
        :param image: Image data
        :param defry: Defry level
        :param prompt: Prompt
        :param mood: Mood
        :raises ValueError: When image is not valid
        :return: AugmentImageInfer
        """
        try:
            image_io = cls._to_bytes_io(image)
            with Image.open(image_io) as img:
                width, height = img.size
                image_io.seek(0)
                image_data = image_io.read()
        except Exception as e:
            raise ValueError("Error when opening image") from e
        if mood and prompt is None:
            prompt = ""
        prompt = f"{mood.value};;{prompt}" if mood else prompt
        return cls(
            req_type=req_type,
            defry=defry,
            image=image_data,
            width=width,
            height=height,
            prompt=prompt,
        )

    async def necessary_headers(self, request_data) -> dict:
        """
        :param request_data:
        :return:
        """
        return {
            "Host": urlparse(self.endpoint).netloc,
            "Accept": "*/*",
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
            'priority': "u=1, i"
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
                      ) -> ImageGenerateResp:
        """
        生成图片
        :param override_headers: the headers to override
        :param session:  session
        :return:
        """
        # Data Build
        request_data = self.model_dump(mode="json", exclude_none=True)
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            # Header
            sess.headers.update(await self.necessary_headers(request_data))
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            try:
                _log_data = deepcopy(request_data)
                _log_data.update({
                    "image": "base64 data"
                })
                logger.debug(f"Request Data: {_log_data}")
                del _log_data
            except Exception as e:
                logger.warning(f"Error when print log data: {e}")
            try:
                assert hasattr(sess, "post"), "session must have post method."
                response = await sess.post(
                    self.base_url,
                    data=json.dumps(request_data).encode("utf-8")
                )
                if response.headers.get('Content-Type') not in ['binary/octet-stream', 'application/x-zip-compressed']:
                    logger.warning(
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
                    if status_code in [429]:
                        # concurrent error
                        raise ConcurrentGenerationError(
                            message=message,
                            request=request_data,
                            code=status_code,
                            response=_msg
                        )
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
                        unzip_content.append((filename, data))
                return ImageGenerateResp(
                    meta=RequestParams(
                        endpoint=self.base_url,
                        raw_request=request_data,
                    ),
                    files=unzip_content
                )
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, maybe SSL error. Try again later!") from exc
            except httpx.HTTPError as exc:
                logger.exception(exc)
                raise SessionHttpError("An HTTPError occurred, maybe SSL error. Try again later!") from exc
            except APIError as e:
                raise e
            except Exception as e:
                logger.opt(exception=e).exception("An Unexpected error occurred")
                raise e
