# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:08
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import base64
import json
import math
import random
from copy import deepcopy
from io import BytesIO
from typing import Optional, Union
from urllib.parse import urlparse
from zipfile import ZipFile

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import BaseModel, ConfigDict, PrivateAttr, field_validator, model_validator, Field
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception
from typing_extensions import override

from ._enum import Model, Sampler, NoiseSchedule, ControlNetModel, Action, UCPreset
from ...schema import ApiBaseModel
from ...._exceptions import APIError, AuthError, ConcurrentGenerationError, SessionHttpError
from ...._response.ai.generate_image import ImageGenerateResp
from ....credential import CredentialBase
from ....utils import try_jsonfy, NovelAiMetadata


class GenerateImageInfer(ApiBaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")

    class Params(BaseModel):
        # Inpaint
        add_original_image: Optional[bool] = False
        mask: Optional[Union[str, bytes]] = None  # img2img,base64

        cfg_rescale: Optional[float] = Field(0, ge=0, le=1, multiple_of=0.02)
        """Prompt Guidance Rescale"""
        controlnet_strength: Optional[float] = Field(1.0, ge=0.1, le=2, multiple_of=0.1)
        """ControlNet Strength"""
        dynamic_thresholding: Optional[bool] = False
        """Reduce artifacts caused by high prompt guidance values."""
        height: Optional[int] = Field(1216, ge=64, le=49152)
        # Img2Img
        image: Optional[Union[str, bytes]] = None  # img2img,base64
        strength: Optional[float] = Field(default=0.5, ge=0.01, le=0.99, multiple_of=0.01)
        noise: Optional[float] = Field(default=0, ge=0, le=0.99, multiple_of=0.01)
        controlnet_condition: Optional[str] = None
        controlnet_model: Optional[ControlNetModel] = None

        n_samples: Optional[int] = Field(1, ge=1, le=8)
        negative_prompt: Optional[str] = ''
        noise_schedule: Optional[NoiseSchedule] = NoiseSchedule.NATIVE

        # Misc
        params_version: Optional[int] = 1
        legacy: Optional[bool] = False
        legacy_v3_extend: Optional[bool] = False

        qualityToggle: Optional[bool] = True
        sampler: Optional[Sampler] = Sampler.K_EULER
        scale: Optional[float] = Field(6.0, ge=0, le=10, multiple_of=0.1)
        """Prompt Guidance"""
        # Seed
        seed: Optional[int] = Field(
            default_factory=lambda: random.randint(0, 4294967295 - 7),
            gt=0,
            le=4294967295 - 7,
        )
        extra_noise_seed: Optional[int] = Field(
            default_factory=lambda: random.randint(0, 4294967295 - 7),
            gt=0,
            le=4294967295 - 7,
        )

        sm: Optional[bool] = False
        sm_dyn: Optional[bool] = False
        steps: Optional[int] = Field(28, ge=1, le=50)
        ucPreset: Optional[UCPreset] = 0
        uncond_scale: Optional[float] = Field(1.0, ge=0, le=1.5, multiple_of=0.05)
        """Undesired Content Strength"""
        width: Optional[int] = Field(832, ge=64, le=49152)

        @model_validator(mode="after")
        def validate_img2img(self):
            image = True if self.image else False
            add_origin = True if self.add_original_image else False
            if image != add_origin:
                raise ValueError('Invalid Model Params For img2img2 mode... image should match add_original_image!')
            return self

        @field_validator('mask')
        def mask_validator(cls, v: Union[str, bytes]):
            if isinstance(v, str) and v.startswith("data:image/"):
                raise ValueError("Invalid image format, must be base64 encoded.")
            if isinstance(v, bytes):
                return base64.b64encode(v).decode("utf-8")
            return v

        @field_validator('image')
        def image_validator(cls, v: Union[str, bytes]):
            if isinstance(v, str) and v.startswith("data:image/"):
                raise ValueError("Invalid image format, must be base64 encoded.")
            if isinstance(v, bytes):
                return base64.b64encode(v).decode("utf-8")
            return v

        @field_validator('width')
        def width_validator(cls, v: int):
            """
            必须是 64 的倍数
            :param v:
            :return:
            """
            if v % 64 != 0:
                raise ValueError("Invalid width, must be multiple of 64.")
            return v

        @field_validator('height')
        def height_validator(cls, v: int):
            """
            必须是 64 的倍数
            :param v:
            :return:
            """
            if v % 64 != 0:
                raise ValueError("Invalid height, must be multiple of 64.")
            return v

    action: Union[str, Action] = Field(Action.GENERATE, description="Mode for img generate")
    input: str = "1girl, best quality, amazing quality, very aesthetic, absurdres"
    model: Optional[Model] = "nai-diffusion-3"
    parameters: Params = Params()
    model_config = ConfigDict(extra="ignore")

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @override
    def model_post_init(self, *args) -> None:
        """
        Post-initialization hook.
        :return:
        """
        if self.parameters.ucPreset == 0:
            # 0: 重型
            self.parameters.negative_prompt += str(
                ", lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, "
                "watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, "
                "username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, "
                "glowing eyes, nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, "
                "extra digit, fewer digits, cropped, worst quality, low quality, normal quality, "
                "jpeg artifacts, signature, watermark, username, blurry"
            )
        elif self.parameters.ucPreset == 1:
            # 1: 轻型
            self.parameters.negative_prompt += (", lowres, jpeg artifacts, worst quality"
                                                ", watermark, blurry, very displeasing")
        elif self.parameters.ucPreset == 2:
            # 2: 人物
            self.parameters.negative_prompt += (", lowres, {bad}, error, fewer, extra, missing, worst quality, "
                                                "jpeg artifacts, bad quality, watermark, unfinished, displeasing, "
                                                "chromatic aberration, signature, extra digits, artistic error, "
                                                "username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched "
                                                "pupils, heart-shaped pupils, glowing eyes")
        if self.parameters.qualityToggle:
            self.input += ", best quality, amazing quality, very aesthetic, absurdres"

    @model_validator(mode="after")
    def validate_model(self):
        if self.action == Action.INFILL and not self.parameters.mask:
            logger.warning("Mask maybe required for infill mode.")
        if self.action != Action.GENERATE:
            self.parameters.extra_noise_seed = self.parameters.seed
        if self.action == Action.IMG2IMG:
            self.parameters.sm = False
            self.parameters.sm_dyn = False
        return self

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate-image"

    def calculate_cost(self, is_opus: bool = False):
        """
        Calculate the Anlas cost of current parameters.

        Parameters
        ----------
        is_opus: `bool`, optional
            If the subscription tier is Opus. Opus accounts have access to free generations.
        """

        steps: int = self.parameters.steps
        n_samples: int = self.parameters.n_samples
        uncond_scale: float = self.parameters.uncond_scale
        strength: float = self.action == "img2img" and self.parameters.strength or 1.0
        smea_factor = self.parameters.sm_dyn and 1.4 or self.parameters.sm and 1.2 or 1.0
        resolution = max(self.parameters.width * self.parameters.height, 65536)

        # For normal resolutions, squre is adjusted to the same price as portrait/landscape
        if math.prod(
                (832, 1216)
        ) < resolution <= math.prod((1024, 1024)):
            resolution = math.prod((832, 1216))
        per_sample = (
                math.ceil(
                    2951823174884865e-21 * resolution
                    + 5.753298233447344e-7 * resolution * steps
                )
                * smea_factor
        )
        per_sample = max(math.ceil(per_sample * strength), 2)

        if uncond_scale != 1.0:
            per_sample = math.ceil(per_sample * 1.3)

        opus_discount = (
                is_opus
                and steps <= 28
                and (resolution <= math.prod((1024, 1024)))
        )
        return per_sample * (n_samples - int(opus_discount))

    @classmethod
    def build(cls,
              prompt: str,
              *,
              model: Union[Model, str] = "nai-diffusion-3",
              action: Union[Action, str] = 'generate',
              negative_prompt: str = "",
              seed: int = None,
              steps: int = 28,
              scale: float = 6.0,
              cfg_rescale: float = 0,
              sampler: Union[Sampler, str] = Sampler.K_EULER,
              width: int = 832,
              height: int = 1216,
              qualityToggle: bool = True,
              ucPreset: Union[UCPreset, int] = UCPreset.TYPE0,
              image: Union[str, bytes] = None,
              add_original_image: bool = None,
              strength: float = None,
              mask: Union[str, bytes] = None,
              controlnet_model: Union[ControlNetModel, str] = None,
              controlnet_condition: str = None,
              **kwargs
              ):
        """
        The build Function, more convenient to create a GenerateImageInfer instance.
        :param ucPreset:  0: Heavy, 1: Light, 2: Character
        :param qualityToggle:  Is quality toggle
        :param prompt: Input prompt for generate image
        :param model: The model for generate image
        :param action: Mode for img generate [generate, img2img, infill]
        :param negative_prompt: The content of negative prompt
        :param seed: The seed for generate image
        :param steps: The steps for generate image
        :param scale: Prompt Guidance
        :param cfg_rescale: Prompt Guidance Rescale 0-1 lower is more creative
        :param sampler: The sampler for generate image
        :param width: 宽
        :param height: 高
        :param image: 图片
        :param add_original_image: 是否添加原始图片
        :param strength: IMG2IMG 强度
        :param mask: Inpainting mask
        :param controlnet_model: 控制网络模型
        :param controlnet_condition: 控制网络条件
        :return: self
        """
        assert isinstance(prompt, str)
        _negative_prompt = negative_prompt
        kwargs.update({
            "negative_prompt": _negative_prompt,
            "seed": seed,
            "steps": steps,
            "scale": scale,
            "cfg_rescale": cfg_rescale,
            "sampler": sampler,
            "width": width,
            "height": height,
            "qualityToggle": qualityToggle,
            "ucPreset": ucPreset,
            "image": image,
            "add_original_image": add_original_image,
            "strength": strength,
            "mask": mask,
            "controlnet_model": controlnet_model,
            "controlnet_condition": controlnet_condition
        })
        # 清理空值
        param = {k: v for k, v in kwargs.items() if v is not None}
        return cls(
            input=prompt,
            model=model,
            action=action,
            parameters=cls.Params(**param)
        )

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
                      ) -> ImageGenerateResp:
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
            _log_data = deepcopy(request_data)
            if self.action == Action.GENERATE:
                logger.debug(f"Request Data: {_log_data}")
            else:
                _log_data.get("parameters", {}).update({
                    "image": "base64 data" if self.parameters.image else None,
                }
                )
                _log_data.get("parameters", {}).update(
                    {
                        "mask": "base64 data" if self.parameters.mask else None,
                    }
                )
                logger.debug(f"Request Data: {_log_data}")
            del _log_data
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
                    if remove_sign:
                        data = NovelAiMetadata.rehash(BytesIO(data), remove_stealth=True)
                        if not isinstance(data, bytes):
                            data = data.getvalue()
                    unzip_content.append((filename, data))
            return ImageGenerateResp(
                meta=ImageGenerateResp.RequestParams(
                    endpoint=self.base_url,
                    raw_request=request_data,
                ),
                files=unzip_content
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
