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

from ._enum import Model, Sampler, NoiseSchedule, ControlNetModel, Action, UCPreset, INPAINTING_MODEL_LIST
from ...schema import ApiBaseModel
from ...._exceptions import APIError, AuthError, ConcurrentGenerationError, SessionHttpError
from ...._response.ai.generate_image import ImageGenerateResp
from ....credential import CredentialBase
from ....utils import try_jsonfy
from PIL import Image


class GenerateImageInfer(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    class Params(BaseModel):
        add_original_image: Optional[bool] = Field(True, description="Overlay Original Image")
        """
        Overlay Original Image.Prevents the existing image from changing,
        but can introduce seams along the edge of the mask.
        叠加原始图像
        防止现有图像发生更改，但可能会沿蒙版边缘引入接缝。
        """
        mask: Optional[Union[str, bytes]] = None
        """Mask for Inpainting"""
        cfg_rescale: Optional[float] = Field(0, ge=0, le=1, multiple_of=0.02)
        """Prompt Guidance Rescale"""
        controlnet_strength: Optional[float] = Field(1.0, ge=0.1, le=2, multiple_of=0.1)
        """ControlNet Strength"""
        dynamic_thresholding: Optional[bool] = False
        """Reduce artifacts caused by high prompt guidance values"""
        height: Optional[int] = Field(1216, ge=64, le=49152)
        """Height For Generate Image"""
        image: Optional[Union[str, bytes]] = None
        """Image for img2img"""
        strength: Optional[float] = Field(default=0.5, ge=0.01, le=0.99, multiple_of=0.01)
        """Strength for img2img"""
        noise: Optional[float] = Field(default=0, ge=0, le=0.99, multiple_of=0.01)
        """Noise for img2img"""
        controlnet_condition: Optional[str] = None
        """ControlNet Condition"""
        controlnet_model: Optional[ControlNetModel] = None
        """ControlNet Model"""
        n_samples: Optional[int] = Field(1, ge=1, le=8)
        """Number of samples"""
        negative_prompt: Optional[str] = ''
        """Negative Prompt"""
        noise_schedule: Optional[NoiseSchedule] = NoiseSchedule.NATIVE
        """Noise Schedule"""
        # Misc
        params_version: Optional[int] = 1
        """Params Version For Request"""
        reference_image: Optional[Union[str, bytes]] = None
        """Reference Image For Vibe Mode"""
        reference_information_extracted: Optional[float] = Field(1,
                                                                 ge=0,
                                                                 le=1,
                                                                 multiple_of=0.01,
                                                                 description="extracting concepts or features"
                                                                 )
        """Reference Information Extracted For Vibe Mode"""
        reference_strength: Optional[float] = Field(0.6,
                                                    ge=0,
                                                    le=1,
                                                    multiple_of=0.01,
                                                    description="the stronger the AI will try to emulate visual cues."
                                                    )
        """Reference Strength For Vibe Mode"""
        legacy: Optional[bool] = False
        # TODO: find out the usage
        legacy_v3_extend: Optional[bool] = False
        # TODO: find out the usage
        qualityToggle: Optional[bool] = True
        """Whether to add the quality prompt"""
        sampler: Optional[Sampler] = Sampler.K_EULER
        """Sampler For Generate Image"""
        scale: Optional[float] = Field(6.0, ge=0, le=10, multiple_of=0.1)
        """Prompt Guidance"""
        # Seed
        seed: Optional[int] = Field(
            default_factory=lambda: random.randint(0, 4294967295 - 7),
            gt=0,
            le=4294967295 - 7,
        )
        """Seed"""
        extra_noise_seed: Optional[int] = Field(
            default_factory=lambda: random.randint(0, 4294967295 - 7),
            gt=0,
            le=4294967295 - 7,
        )
        """Extra Noise Seed"""
        sm: Optional[bool] = False
        # TODO: find out the usage
        sm_dyn: Optional[bool] = False
        # TODO: find out the usage
        steps: Optional[int] = Field(28, ge=1, le=50)
        """Steps"""
        ucPreset: Optional[UCPreset] = 0
        """The Negative Prompt Preset"""
        uncond_scale: Optional[float] = Field(1.0, ge=0, le=1.5, multiple_of=0.05)
        """Undesired Content Strength"""
        width: Optional[int] = Field(832, ge=64, le=49152)
        """Width For Image"""

        @staticmethod
        def resize_image(image: Union[str, bytes], width: int, height: int):
            """
            Resize the image to the specified size.
            :param image: The image to be resized
            :param width: The width of the image
            :param height: The height of the image
            :return: The resized image
            """
            if isinstance(image, str):
                image = base64.b64decode(image)
            open_image = Image.open(BytesIO(image)).convert("RGBA")
            # 如果尺寸相同，直接返回
            if open_image.width == width and open_image.height == height:
                logger.debug("Image size is same, return directly.")
                if isinstance(image, bytes):
                    return base64.b64encode(image).decode("utf-8")
                return image
            open_image = open_image.resize((width, height), Image.Resampling.BICUBIC)
            buffered = BytesIO()
            open_image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

        @staticmethod
        def add_image_to_black_background(image: Union[str, bytes], width: int = 448, height: int = 448):
            """
            缩放图像到指定的黑色透明背景上，使其尽可能大且保持比例。
            :param image: 图像
            :param width: 宽
            :param height: 高
            :return: 新图像
            """
            if isinstance(image, str):
                image = base64.b64decode(image)

            open_image = Image.open(BytesIO(image)).convert("RGBA")
            # 如果尺寸相同，直接返回
            if open_image.width == width and open_image.height == height:
                return base64.b64encode(image).decode("utf-8")

            # 计算正确的缩放因子
            width_ratio = width / open_image.width
            height_ratio = height / open_image.height
            ratio = min(width_ratio, height_ratio)

            new_image_size = (int(open_image.width * ratio), int(open_image.height * ratio))
            open_image = open_image.resize(new_image_size, Image.Resampling.BICUBIC)

            # 创建一个黑色透明背景的新图像，颜色深度32位
            new_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

            # 计算居中位置
            position = ((width - open_image.width) // 2, (height - open_image.height) // 2)

            # 粘贴图像
            new_image.paste(open_image, position)

            buffered = BytesIO()
            new_image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Validators
        @model_validator(mode="after")
        def image_validator(self):
            if isinstance(self.image, str) and self.image.startswith("data:"):
                raise ValueError("Invalid `image` format, must be base64 encoded directly.")
            if isinstance(self.reference_image, str) and self.reference_image.startswith("data:"):
                raise ValueError("Invalid `reference_image` format, must be base64 encoded directly.")
            if isinstance(self.mask, str) and self.mask.startswith("data:"):
                raise ValueError("Invalid `mask` format, must be base64 encoded directly.")
            if isinstance(self.image, bytes):
                self.image = base64.b64encode(self.image).decode("utf-8")
            if isinstance(self.reference_image, bytes):
                self.reference_image = base64.b64encode(self.reference_image).decode("utf-8")
            if isinstance(self.mask, bytes):
                self.mask = base64.b64encode(self.mask).decode("utf-8")
            if self.image is not None:
                self.image = self.resize_image(self.image, self.width, self.height)
            if self.reference_image is not None:
                self.reference_image = self.add_image_to_black_background(self.reference_image, width=448, height=448)
            return self

        @field_validator('width')
        def width_validator(cls, v: int):
            """
            Must be multiple of 64
            :param v:
            :return: fixed value
            """
            if v % 64 != 0:
                raise ValueError("Invalid width, must be multiple of 64.")
            return v

        @field_validator('height')
        def height_validator(cls, v: int):
            """
            Must be multiple of 64
            :param v:
            :return: fixed value
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
        Simulate website logic to add negative prompt based on ucPreset and qualityToggle.
        :param args: Any
        :return: None
        """
        if self.parameters.negative_prompt is None:
            self.parameters.negative_prompt = ""
        if self.parameters.ucPreset == 0:
            # 0: 重型
            self.parameters.negative_prompt = (
                "lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, "
                "watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, "
                "username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, "
                "glowing eyes, nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, "
                "extra digit, fewer digits, cropped, worst quality, low quality, normal quality, "
                f"jpeg artifacts, signature, watermark, username, blurry "
                f",{self.parameters.negative_prompt}"
            )
        elif self.parameters.ucPreset == 1:
            # 1: 轻型
            self.parameters.negative_prompt = (f"lowres, jpeg artifacts, worst quality, watermark, blurry, "
                                               f"very displeasing"
                                               f",{self.parameters.negative_prompt}")
        elif self.parameters.ucPreset == 2:
            # 2: 人物
            self.parameters.negative_prompt = ("lowres, {bad}, error, fewer, extra, missing, worst quality, "
                                               "jpeg artifacts, bad quality, watermark, unfinished, displeasing, "
                                               "chromatic aberration, signature, extra digits, artistic error, "
                                               "username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched "
                                               f"pupils, heart-shaped pupils, glowing eyes "
                                               f",{self.parameters.negative_prompt}")
        if self.parameters.qualityToggle:
            self.input += ", best quality, amazing quality, very aesthetic, absurdres"

    @model_validator(mode="after")
    def validate_model(self):
        """
        Check the conflict between parameters and simulate website logic.
        :return: self
        """
        # Text2Img mode
        if self.action == Action.GENERATE:
            if self.parameters.image is not None:
                raise ValueError("image is not required for non-generate mode.")
            if self.parameters.mask is not None:
                raise ValueError("mask is not required for non-generate mode.")
        # Infill mode
        if self.action == Action.INFILL:
            if self.model not in INPAINTING_MODEL_LIST:
                raise ValueError(f"You must use {INPAINTING_MODEL_LIST}")
            if not self.parameters.mask:
                logger.warning("Mask maybe required for infill mode!")
        # Sync seed
        if self.action != Action.GENERATE:
            self.parameters.extra_noise_seed = self.parameters.seed
        # Img2Img mode
        if self.action == Action.IMG2IMG:
            if self.parameters.sm_dyn is True:
                logger.warning("sm_dyn is disabled when sm in Img2Img mode.")
            if self.parameters.sm is True:
                logger.warning("sm is disabled when sm_dyn in Img2Img mode.")
            self.parameters.sm = False
            self.parameters.sm_dyn = False
            if self.parameters.image is None:
                raise ValueError("image is must required for img2img mode.")
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
              ucPreset: Union[UCPreset, int] = UCPreset.TYPE0,
              steps: int = 28,
              seed: int = None,
              scale: float = 5.0,
              cfg_rescale: float = 0,
              sampler: Union[Sampler, str] = None,
              width: int = 832,
              height: int = 1216,
              qualityToggle: bool = None,
              image: Union[str, bytes] = None,
              noise: float = 0,
              reference_image: Union[str, bytes] = None,
              reference_strength: float = None,
              reference_information_extracted: float = None,
              add_original_image: bool = True,
              strength: float = None,
              mask: Union[str, bytes] = None,
              controlnet_model: Union[ControlNetModel, str] = None,
              controlnet_condition: str = None,
              sm: bool = False,
              sm_dyn: bool = False,
              uncond_scale: float = None,
              **kwargs
              ):
        """
        The build function, more convenient to create a GenerateImageInfer instance.
        构建函数，更方便地创建一个GenerateImageInfer实例。
        :param ucPreset: 0: Heavy, 1: Light, 2: Character
                        0: 重量级, 1: 轻量级, 2: 角色
        :param qualityToggle: add the quality prompt or not.
                              是否添加质量提示。
        :param prompt: input prompt for generation.
                       生成的输入提示。
        :param model: select a model.
                      选择一个模型。
        :param action: mode for image generation [generate, img2img, infill].
                       图像生成模式 [生成, 图像到图像, 填充]。
        :param negative_prompt: the content of negative prompt.
                                负面提示的内容。
        :param seed: the seed for generate image.
                     生成图像的种子。
        :param steps: the steps for generate image.
                      生成图像的步骤。
        :param scale: the scale for generate image.
                      生成图像的比例。
        :param cfg_rescale: prompt guidance rescale 0-1 lower is more creative.
                            提示引导的重新缩放0-1，越低则越富有创造性。
        :param sampler: the sampler for generate image.
                        生成图像的采样器。
        :param width: the width of the image.
                      图像的宽度。
        :param height: the height of the image.
                       图像的高度。
        :param image: the input image.
                      输入图像。
        :param noise: the noise to be added in the image.
                      要添加到图像中的噪声。
        :param reference_image: the reference image for Vibe mode.
                                Vibe模式的参考图像。
        :param reference_strength: the strength of the reference image used in Vibe mode.
                                   在Vibe模式中使用的参考图像的强度。
        :param reference_information_extracted: whether to extract concept or features, for Vibe mode.
                                                是否提取概念或特征，用于Vibe模式。
        :param add_original_image: Overlay Original Image. Prevents the existing image from changing, only for IMG2IMG mode.
                                   叠加原始图像。防止现有图像发生更改，仅适用于IMG2IMG模式。
        :param strength: the strength of IMG2IMG mode.
                         IMG2IMG模式的强度。
        :param mask: the inpainting mask.
                     纹理绘制掩码。
        :param controlnet_model: the model used for the control network.
                                 用于控制网络的模型。
        :param controlnet_condition: the condition used for the control network.
                                     用于控制网络的条件。
        :param sm: whether to use sm.
                    是否使用sm。
        :param sm_dyn: whether to use dynamic sm.
                       是否使用动态sm。
        :param uncond_scale: the strength of the unrelated content.
                             无关内容的强度。
        :param kwargs: any additional parameters.
                       其他任何参数。

        :return: self
        返回：自身
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
            "add_original_image": add_original_image,
            "mask": mask,
            "controlnet_model": controlnet_model,
            "controlnet_condition": controlnet_condition,
            "sm_dyn": sm_dyn,
            "sm": sm,
            "uncond_scale": uncond_scale,
        })
        kwargs.update(
            {
                "reference_image": reference_image,
                "reference_strength": reference_strength,
                "reference_information_extracted": reference_information_extracted,
            }
        )
        kwargs.update(
            {
                "image": image,
                "strength": strength,
                "noise": noise,
            }
        )
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
                      ) -> ImageGenerateResp:
        """
        生成图片
        :param override_headers: the headers to override
        :param session:  session
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
            _log_data.get("parameters", {}).update({
                "image": "base64 data" if self.parameters.image else None,
                "mask": "base64 data" if self.parameters.mask else None,
                "reference_image": "base64 data" if self.parameters.reference_image else None,
            })
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
