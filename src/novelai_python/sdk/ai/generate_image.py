# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午11:21
# @Author  : sudoskys
# @File    : generate_image.py
# @Software: PyCharm
import json
import random
from io import BytesIO
from typing import Optional, Union, Literal
from zipfile import ZipFile

import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from novelai_python.utils import NovelAiMetadata
from pydantic import BaseModel, ConfigDict, PrivateAttr, field_validator, model_validator

from ..._exceptions import APIError, AuthError
from ..._response import ImageGenerateResp
from ...credential import JwtCredential
from ...utils import try_jsonfy


class GenerateImageInfer(BaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")
    _charge: bool = PrivateAttr(False)

    class Params(BaseModel):
        add_original_image: Optional[bool] = False
        cfg_rescale: Optional[int] = 0
        controlnet_strength: Optional[int] = 1
        dynamic_thresholding: Optional[bool] = False
        height: Optional[int] = 1216
        image: Optional[str] = None  # img2img,base64
        legacy: Optional[bool] = False
        legacy_v3_extend: Optional[bool] = False
        n_samples: Optional[int] = 1
        negative_prompt: Optional[str] = (
            "nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, "
            "watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, "
            "username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, "
            "glowing eyes, nsfw, lowres, bad anatomy, bad hands, text, error,                        missing fingers, "
            "extra digit, fewer digits, cropped,                        worst quality, low quality, normal quality, "
            "jpeg artifacts, signature, watermark, username, blurry"
        )
        noise_schedule: Optional[Union[str, Literal['native', 'polyexponential', 'exponential']]] = "native"
        params_version: Optional[int] = 1
        qualityToggle: Optional[bool] = True
        sampler: Optional[str] = "k_euler"
        scale: Optional[int] = 5
        seed: Optional[int] = -1
        sm: Optional[bool] = False
        sm_dyn: Optional[bool] = False
        steps: Optional[int] = 28
        ucPreset: Optional[int] = 0
        uncond_scale: Optional[int] = 1
        width: Optional[int] = 832

        @field_validator('seed')
        def seed_validator(cls, v: int):
            if v == -1:
                v = random.randint(0, 2 ** 32 - 1)
            return v

        @model_validator(mode="after")
        def validate_img2img(self):

            image = True if self.image else False
            add_origin = True if self.add_original_image else False
            if image != add_origin:
                raise ValueError('Invalid Model Params For img2img2 mode... image should match add_original_image!')
            return self

        @field_validator('sampler')
        def sampler_validator(cls, v: str):
            if v not in ["k_euler", "k_euler_ancestral", 'k_dpmpp_2s_ancestral', "k_dpmpp_2m", "k_dpmpp_sde",
                         "ddim_v3"]:
                raise ValueError("Invalid sampler.")
            return v

        @field_validator('noise_schedule')
        def noise_schedule_validator(cls, v: str):
            if v not in ["native", "karras", "exponential", "polyexponential"]:
                raise ValueError("Invalid noise_schedule.")
            return v

        @field_validator('steps')
        def steps_validator(cls, v: int):
            if v > 28:
                logger.warning(f"steps {v} > 28, maybe charge more.")
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

        @field_validator('n_samples')
        def n_samples_validator(cls, v: int):
            """
            小于 8
            :param v:
            :return:
            """
            if v > 8:
                raise ValueError("Invalid n_samples, must be less than 8.")
            return v

    action: Union[str, Literal["generate", "img2img"]] = "generate"
    input: str = "1girl, best quality, amazing quality, very aesthetic, absurdres"
    model: Optional[str] = "nai-diffusion-3"
    parameters: Params = Params()
    model_config = ConfigDict(extra="ignore")

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate-image"

    @property
    def charge(self):
        return self._charge

    @charge.setter
    def charge(self, value):
        self._charge = value

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @staticmethod
    def valid_wh():
        """
        宽高
        :return:
        """
        return [
            (832, 1216),
            (1216, 832),
            (1024, 1024),
        ]

    def validate_charge(self):
        if self.parameters.steps > 28 and not self.charge:
            raise ValueError("steps must be less than 28 for free users.")
        if (self.parameters.width, self.parameters.height) not in self.valid_wh() and not self.charge:
            raise ValueError("Invalid size, must be one of 832x1216, 1216x832, 1024x1024 for free users.")
        if self.parameters.n_samples != 1 and not self.charge:
            raise ValueError("n_samples must be 1 for free users.")
        return self

    @classmethod
    def build(cls,
              prompt: str,
              *,
              model: str = "nai-diffusion-3",
              action: Literal['generate', 'img2img'] = 'generate',
              negative_prompt: Optional[str] = None,
              override_negative_prompt: bool = False,
              seed: int = -1,
              steps: int = 28,
              cfg_rescale: int = 0,
              sampler: str = "k_euler",
              width: int = 832,
              height: int = 1216,
              ):
        """
        正负面, step, cfg, 采样方式, seed
        :param override_negative_prompt:
        :param prompt:
        :param model:
        :param action: Mode for img generate
        :param negative_prompt:
        :param seed:
        :param steps:
        :param cfg_rescale:
        :param sampler:
        :param width:
        :param height:
        :return: self
        """
        assert isinstance(prompt, str)
        _negative_prompt = ("nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, "
                            "bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, "
                            "extra digits, artistic error, username, scan, [abstract], bad anatomy, bad hands, "
                            "@_@, mismatched pupils, heart-shaped pupils, glowing eyes, nsfw, lowres, bad anatomy, "
                            "bad hands, text, error,missing fingers, extra digit, fewer digits, cropped,"
                            "worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, "
                            "username, blurry")
        if override_negative_prompt:
            _negative_prompt = negative_prompt
        else:
            _negative_prompt = f"{_negative_prompt}, {negative_prompt}"
        param = {
            "negative_prompt": _negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg_rescale": cfg_rescale,
            "sampler": sampler,
            "width": width,
            "height": height,
        }
        # 清理空值
        param = {k: v for k, v in param.items() if v is not None}
        return cls(
            input=prompt,
            model=model,
            action=action,
            parameters=cls.Params(**param)
        )

    async def generate(self, session: Union[AsyncSession, JwtCredential],
                       *,
                       remove_sign: bool = False) -> ImageGenerateResp:
        """
        生成图片
        :param session:  session
        :param remove_sign:  移除追踪信息
        :return:
        """
        if isinstance(session, JwtCredential):
            session = session.session
        request_data = self.model_dump(exclude_none=True)
        logger.debug(f"Request Data: {request_data}")
        try:
            assert hasattr(session, "post"), "session must have post method."
            response = await session.post(
                self.base_url,
                data=json.dumps(request_data).encode("utf-8")
            )
            if response.headers.get('Content-Type') not in ['binary/octet-stream', 'application/x-zip-compressed']:
                try:
                    _msg = response.json()
                except Exception:
                    raise APIError(
                        message=f"Unexpected content type: {response.headers.get('Content-Type')}",
                        request=request_data,
                        status_code=response.status_code,
                        response=try_jsonfy(response.content)
                    )
                status_code = _msg.get("statusCode", response.status_code)
                message = _msg.get("message", "Unknown error")
                if status_code in [400, 401, 402]:
                    # 400 : validation error
                    # 401 : unauthorized
                    # 402 : payment required
                    # 409 : conflict
                    raise AuthError(message, request=request_data, status_code=status_code, response=_msg)
                if status_code in [409]:
                    # conflict error
                    raise APIError(message, request=request_data, status_code=status_code, response=_msg)
                raise APIError(message, request=request_data, status_code=status_code, response=_msg)
            zip_file = ZipFile(BytesIO(response.content))
            unzip_content = []
            with zip_file as zf:
                file_list = zf.namelist()
                if not file_list:
                    raise APIError(
                        message="No file in zip",
                        request=request_data,
                        status_code=response.status_code,
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
        except httpx.HTTPError as exc:
            raise RuntimeError(f"An HTTP error occurred: {exc}")
        except APIError as e:
            raise e
        except Exception as e:
            logger.opt(exception=e).exception("An Unexpected error occurred")
            raise e
