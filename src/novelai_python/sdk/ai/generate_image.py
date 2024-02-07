# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午11:21
# @Author  : sudoskys
# @File    : generate_image.py
# @Software: PyCharm
import json
import math
import random
from io import BytesIO
from typing import Optional, Union, Literal
from zipfile import ZipFile

import httpx
from curl_cffi.requests import AsyncSession, RequestsError
from loguru import logger
from pydantic import BaseModel, ConfigDict, PrivateAttr, field_validator, model_validator, Field
from typing_extensions import override

from ..._exceptions import APIError, AuthError
from ..._response import ImageGenerateResp
from ...utils import try_jsonfy, NovelAiMetadata
from ...credential import CredentialBase


class GenerateImageInfer(BaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")
    _charge: bool = PrivateAttr(False)

    class Params(BaseModel):
        # Inpaint
        add_original_image: Optional[bool] = False
        mask: Optional[str] = None

        cfg_rescale: Optional[float] = Field(0, ge=0, le=1, multiple_of=0.02)
        controlnet_strength: Optional[float] = Field(1.0, ge=0.1, le=2, multiple_of=0.1)
        dynamic_thresholding: Optional[bool] = False
        height: Optional[int] = Field(1216, ge=64, le=49152)
        # Img2Img
        image: Optional[str] = None  # img2img,base64
        strength: Optional[float] = Field(default=0.3, ge=0.01, le=0.99, multiple_of=0.01)
        noise: Optional[float] = Field(default=0, ge=0, le=0.99, multiple_of=0.01)
        controlnet_condition: Optional[str] = None
        controlnet_model: Optional[str] = None

        n_samples: Optional[int] = Field(1, ge=1, le=8)
        negative_prompt: Optional[str] = ''
        noise_schedule: Optional[Union[str, Literal['native', 'polyexponential', 'exponential']]] = "native"

        # Misc
        params_version: Optional[int] = 1
        legacy: Optional[bool] = False
        legacy_v3_extend: Optional[bool] = False

        qualityToggle: Optional[bool] = True
        sampler: Optional[str] = "k_euler"
        scale: Optional[float] = Field(6.0, ge=0, le=10, multiple_of=0.1)
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
        ucPreset: Optional[Literal[0, 1, 2, 3]] = 0
        uncond_scale: Optional[float] = Field(1.0, ge=0, le=1.5, multiple_of=0.05)
        width: Optional[int] = Field(832, ge=64, le=49152)

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

    action: Union[str, Literal["generate", "img2img", "infill"]] = "generate"
    input: str = "1girl, best quality, amazing quality, very aesthetic, absurdres"
    model: Optional[str] = "nai-diffusion-3"
    parameters: Params = Params()
    model_config = ConfigDict(extra="ignore")

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

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate-image"

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
              model: str = "nai-diffusion-3",
              action: Literal['generate', 'img2img'] = 'generate',
              negative_prompt: str = "",
              seed: int = None,
              steps: int = 28,
              cfg_rescale: int = 0,
              sampler: str = "k_euler",
              width: int = 832,
              height: int = 1216,
              qualityToggle: bool = True,
              ucPreset: int = 0,
              ):
        """
        正负面, step, cfg, 采样方式, seed
        :param ucPreset:  0: 重型, 1: 轻型, 2: 人物
        :param qualityToggle:  是否开启质量
        :param prompt: 输入
        :param model: 模型
        :param action: Mode for img generate [generate, img2img, infill]
        :param negative_prompt: 负面
        :param seed: 随机种子
        :param steps: 步数
        :param cfg_rescale: 0-1
        :param sampler: 采样方式
        :param width: 宽
        :param height: 高
        :return: self
        """
        assert isinstance(prompt, str)
        _negative_prompt = negative_prompt
        param = {
            "negative_prompt": _negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg_rescale": cfg_rescale,
            "sampler": sampler,
            "width": width,
            "height": height,
            "qualityToggle": qualityToggle,
            "ucPreset": ucPreset,
        }
        # 清理空值
        param = {k: v for k, v in param.items() if v is not None}
        return cls(
            input=prompt,
            model=model,
            action=action,
            parameters=cls.Params(**param)
        )

    async def generate(self, session: Union[AsyncSession, "CredentialBase"],
                       *,
                       remove_sign: bool = False) -> ImageGenerateResp:
        """
        生成图片
        :param session:  session
        :param remove_sign:  移除追踪信息
        :return:
        """
        if isinstance(session, CredentialBase):
            session = await session.get_session()
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
        except RequestsError as exc:
            logger.exception(exc)
            raise RuntimeError(f"An AsyncSession error occurred: {exc}")
        except httpx.HTTPError as exc:
            raise RuntimeError(f"An HTTP error occurred: {exc}")
        except APIError as e:
            raise e
        except Exception as e:
            logger.opt(exception=e).exception("An Unexpected error occurred")
            raise e
