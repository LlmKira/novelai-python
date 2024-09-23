# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:08
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import base64
import json
import random
from copy import deepcopy
from io import BytesIO
from typing import Optional, Union, Tuple, List
from urllib.parse import urlparse
from zipfile import ZipFile

import curl_cffi
import cv2
import httpx
import numpy as np
from PIL import Image
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import BaseModel, ConfigDict, PrivateAttr, field_validator, model_validator, Field
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception
from typing_extensions import override

from novelai_python.sdk.ai._cost import CostCalculator
from novelai_python.sdk.ai._enum import Model, Sampler, NoiseSchedule, ControlNetModel, Action, UCPreset, \
    INPAINTING_MODEL_LIST, get_default_noise_schedule, get_supported_noise_schedule, get_default_uc_preset, \
    ModelTypeAlias, ImageBytesTypeAlias, UCPresetTypeAlias
from ...schema import ApiBaseModel
from ...._exceptions import APIError, AuthError, ConcurrentGenerationError, SessionHttpError
from ...._response.ai.generate_image import ImageGenerateResp, RequestParams
from ....credential import CredentialBase
from ....utils import try_jsonfy


def is_multiple_of_01(num, precision=1e-10):
    remainder = num % 0.01
    return abs(remainder) < precision or abs(0.01 - remainder) < precision


class Params(BaseModel):
    add_original_image: Optional[bool] = Field(True, description="Overlay Original Image")
    """
    Overlay Original Image.Prevents the existing image from changing,
    but can introduce seams along the edge of the mask.
    叠加原始图像
    防止现有图像发生更改，但可能会沿蒙版边缘引入接缝。
    """
    mask: ImageBytesTypeAlias = None
    """Mask for Inpainting"""
    cfg_rescale: Optional[float] = Field(0, ge=0, le=1, multiple_of=0.02)
    """Prompt Guidance Rescale"""
    controlnet_strength: Optional[float] = Field(1.0, ge=0.1, le=2, multiple_of=0.1)
    """ControlNet Strength"""
    dynamic_thresholding: Optional[bool] = False
    """Decrisp:Reduce artifacts caused by high prompt guidance values"""
    height: Optional[int] = Field(1216, ge=64, le=49152)
    """Height For Generate Image"""
    image: ImageBytesTypeAlias = None
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
    noise_schedule: Optional[NoiseSchedule] = None
    """Noise Schedule"""
    # Misc
    params_version: Optional[int] = 1
    """Params Version For Request"""
    reference_image_multiple: Optional[List[Union[str, bytes]]] = None
    """Reference Image For Vibe Mode"""
    reference_information_extracted_multiple: Optional[List[float]] = None
    """Reference Information Extracted For Vibe Mode"""

    @field_validator('reference_information_extracted_multiple')
    def reference_information_extracted_multiple_validator(cls, v):
        # List[Field(..., ge=0, le=1, multiple_of=0.01)]
        if v is None:
            return v
        for i in v:
            if not 0 <= i <= 1:
                raise ValueError("Invalid reference_information_extracted_multiple, must be in [0, 1].")
            if not is_multiple_of_01(i):
                raise ValueError("Invalid reference_information_extracted_multiple, must be multiple of 0.01.")
        return v

    reference_strength_multiple: Optional[List[float]] = None

    @field_validator('reference_strength_multiple')
    def reference_strength_multiple_validator(cls, v):
        # Field(0.6,ge=0,le=1,multiple_of=0.01,description="the stronger the AI will try to emulate visual cues.")
        if v is None:
            return v
        for i in v:
            if not 0 <= i <= 1:
                raise ValueError("Invalid reference_strength_multiple, must be in [0, 1].")
            if not is_multiple_of_01(i):
                raise ValueError("Invalid reference_strength_multiple, must be multiple of 0.01.")
        return v

    """Reference Strength For Vibe Mode"""
    legacy: Optional[bool] = False
    # TODO: find out the usage
    legacy_v3_extend: Optional[bool] = False
    # TODO: find out the usage
    qualityToggle: Optional[bool] = True
    """Whether to add the quality prompt"""
    sampler: Optional[Sampler] = Sampler.K_EULER_ANCESTRAL
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
    skip_cfg_above_sigma: Optional[int] = None
    """Variety Boost, a new feature to improve the diversity of samples."""
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
    steps: Optional[int] = Field(23, ge=1, le=50)
    """Steps"""
    ucPreset: UCPresetTypeAlias = Field(None, ge=0)
    """The Negative Prompt Preset, Bigger or equal to 0"""
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
    def add_image_to_black_background(
            image: Union[str, bytes],
            target_size: Tuple[int, int] = (448, 448),
            transparency: bool = False
    ):

        """
        缩放图像到指定的黑色透明背景上，使其尽可能大且保持比例。
        :param transparency: 是否透明
        :param image: 图像
        :param target_size: 目标尺寸
        :return: 新图像
        """

        if isinstance(image, str):
            image = base64.b64decode(image)
            # Decode the image from the base64 string
        npimg = np.frombuffer(image, np.uint8)
        # Load the image with OpenCV
        img = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)
        # Calculate the aspect ratio (keeping aspect ratio)
        ratio = min(target_size[0] / img.shape[1], target_size[1] / img.shape[0])
        new_image_size = (int(img.shape[1] * ratio), int(img.shape[0] * ratio))
        # Resize the image
        img = cv2.resize(img, new_image_size, interpolation=cv2.INTER_LINEAR)
        # Check if the image has alpha channel (transparency)
        if img.shape[2] == 3:  # no alpha channel, add one
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        # Create new image with black background
        delta_w = target_size[0] - img.shape[1]
        delta_h = target_size[1] - img.shape[0]
        top, bottom = delta_h // 2, delta_h - (delta_h // 2)
        left, right = delta_w // 2, delta_w - (delta_w // 2)
        # If the transparency flag is set the background is transparent, otherwise it is black
        color = [0, 0, 0, 0] if transparency else [0, 0, 0, 255]
        # Add padding to the image
        new_img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        # Convert the image to base64
        _, buffer = cv2.imencode(".png", new_img)
        # buffer here is a numpy array, convert it to bytes
        image_bytes = buffer.tobytes()
        return base64.b64encode(image_bytes).decode("utf-8")

    # Validators
    @model_validator(mode="after")
    def image_validator(self):
        # Noise schedule check
        if self.noise_schedule is None:
            self.noise_schedule = get_default_noise_schedule(self.sampler)
        supported_noise_schedule = get_supported_noise_schedule(self.sampler)
        if supported_noise_schedule:
            if self.noise_schedule not in supported_noise_schedule:
                raise ValueError(f"Invalid noise_schedule, must be one of {supported_noise_schedule}")
        else:
            logger.warning(f"Inactive sampler {self.sampler} does not support noise_schedule.")
        # Check the noise value
        if self.sampler:
            if self.sampler in [Sampler.DDIM, Sampler.DDIM_V3]:
                self.sm = False
                self.sm_dyn = False
                if self.sm_dyn or self.sm:
                    logger.warning("sm and sm_dyn is disabled when using ddim sampler.")
            if self.sampler in [Sampler.NAI_SMEA_DYN]:
                self.sm = True
                self.sm_dyn = True
                if not self.sm_dyn:
                    logger.warning("sm and sm_dyn is enabled when using nai_smea_dyn sampler.")
        # Make sure the image is base64 encoded
        if isinstance(self.image, str) and self.image.startswith("data:"):
            raise ValueError("Invalid `image` format, must be base64 encoded directly.")
        if isinstance(self.mask, str) and self.mask.startswith("data:"):
            raise ValueError("Invalid `mask` format, must be base64 encoded directly.")
        if isinstance(self.image, bytes):
            self.image = base64.b64encode(self.image).decode("utf-8")
        # Resize the image to the specified size
        if self.reference_image_multiple is not None:
            new_images = []
            for reference_image in self.reference_image_multiple:
                if isinstance(reference_image, str):
                    if reference_image.startswith("data:"):
                        raise ValueError("Invalid `reference_image` format, must be base64 encoded directly.")
                    new_images.append(reference_image)
                elif isinstance(reference_image, bytes):
                    new_image = self.add_image_to_black_background(reference_image,
                                                                   target_size=(448, 448),
                                                                   transparency=True)
                    if isinstance(new_image, bytes):
                        new_image = base64.b64encode(new_image).decode("utf-8")
                    new_images.append(new_image)
                else:
                    raise ValueError("Invalid `reference_image` format, must be base64 encoded directly.")
            self.reference_image_multiple = new_images
        # 如果都不是 None 时，比较他们的长度
        if all([self.reference_strength_multiple,
                self.reference_image_multiple,
                self.reference_information_extracted_multiple]):
            if len(self.reference_strength_multiple) != len(self.reference_image_multiple) != len(
                    self.reference_information_extracted_multiple):
                raise ValueError(
                    f"All three reference_* must be of equal length, "
                    f"strength:{len(self.reference_strength_multiple)}, "
                    f"image:{len(self.reference_image_multiple)}, "
                    f"information:{len(self.reference_information_extracted_multiple)}"
                )
            if len(self.reference_image_multiple) > 16:
                raise ValueError("The maximum number of reference images is 16")
        # 如果有一个存在，其他都必须存在
        ref_items = [self.reference_strength_multiple,
                     self.reference_image_multiple,
                     self.reference_information_extracted_multiple]
        if any(ref_items) and not all(ref_items):
            raise ValueError("All fields must be present together or none should be present")

        if isinstance(self.mask, bytes):
            self.mask = base64.b64encode(self.mask).decode("utf-8")
        if self.image is not None:
            self.image = self.resize_image(self.image, self.width, self.height)
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


class GenerateImageInfer(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    action: Union[str, Action] = Field(Action.GENERATE, description="Mode for img generate")
    input: str = "1girl, best quality, amazing quality, very aesthetic, absurdres"
    model: ModelTypeAlias = "nai-diffusion-3"
    parameters: Params = Params()
    model_config = ConfigDict(extra="ignore")

    @override
    def model_post_init(self, *args) -> None:
        """
        Post-initialization hook.
        Simulate website logic to add negative prompt based on ucPreset and qualityToggle.
        :param args: Any
        :return: None
        """
        # Must be a string
        if self.parameters.negative_prompt is None:
            self.parameters.negative_prompt = ""

        # Add negative prompt based on ucPreset
        if self.parameters.ucPreset is not None:
            default_negative_prompt = get_default_uc_preset(self.model, self.parameters.ucPreset)
            self.parameters.negative_prompt = ", ".join(
                filter(None, [default_negative_prompt, self.parameters.negative_prompt])
            )

        # Add quality prompt
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
        :param is_opus: Whether the account is Opus.
        :return: The cost of the current parameters.
        :raises ValueError: If failed to calculate cost.
        """
        try:
            return CostCalculator.calculate(
                width=self.parameters.width,
                height=self.parameters.height,
                steps=self.parameters.steps,
                model=self.model,
                image=self.parameters.image,
                n_samples=self.parameters.n_samples,
                account_tier=3 if is_opus else 1,
                strength=self.parameters.strength,
                sampler=self.parameters.sampler,
                is_sm_enabled=self.parameters.sm,
                is_sm_dynamic=self.parameters.sm_dyn,
                is_account_active=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to calculate cost") from e

    @classmethod
    def build(cls,
              prompt: str,
              *,
              model: Union[Model, str] = "nai-diffusion-3",
              action: Union[Action, str] = 'generate',
              negative_prompt: str = "",
              ucPreset: UCPresetTypeAlias = UCPreset.TYPE0,
              steps: int = 28,
              seed: int = None,
              scale: float = 5.0,
              cfg_rescale: float = 0,
              sampler: Union[Sampler, str] = None,
              width: int = 832,
              height: int = 1216,
              qualityToggle: bool = None,
              image: Union[str, bytes] = None,
              decrisp_mode: bool = False,
              variety_boost: bool = False,
              noise: float = 0,
              noise_schedule: Union[NoiseSchedule, str] = None,
              reference_image_multiple: List[Union[str, bytes]] = None,
              reference_strength_multiple: List[float] = None,
              reference_information_extracted_multiple: List[float] = None,
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
        :param decrisp_mode: Reduce artifacts caused by high prompt guidance values.
                            减少由高提示引导值引起的伪影。
        :param variety_boost: A new feature to improve the diversity of samples.
                            Variety Boost means your negative prompt will only be used after the body shape has been decided.
                            一项新功能，用于提高样本的多样性。但是，这意味着您的负面提示只会在身体形状确定后使用。
        :param reference_information_extracted_multiple:  The reference information extracted for Vibe mode.
                                                            Vibe模式的提取的参考信息。
        :param reference_image_multiple: The reference image for Vibe mode.
                                            Vibe模式的参考图像。
        :param reference_strength_multiple: The strength of the reference image used in Vibe mode.
                                            在Vibe模式中使用的参考图像的强度。
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
        :param noise_schedule: the noise schedule for generate image.
                    生成图像的噪声计划。
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
            "noise_schedule": noise_schedule,
        })

        def _merge_param(v1, v2):
            _list = []
            if isinstance(v1, list):
                _list.extend(v1)
            else:
                if v1 is not None:
                    _list.append(v1)
            if isinstance(v2, list):
                _list.extend(v2)
            else:
                if v2 is not None:
                    _list.append(v2)
            return _list

        if reference_image:
            logger.warning(
                "reference_image is deprecated, use reference_image_multiple instead."
            )
            reference_image_multiple = _merge_param(
                reference_image, reference_image_multiple
            )
        if reference_strength:
            logger.warning(
                "reference_strength is deprecated, use reference_strength_multiple instead."
            )
            reference_strength_multiple = _merge_param(
                reference_strength, reference_strength_multiple
            )
        if reference_information_extracted:
            logger.warning(
                "reference_information_extracted is deprecated, use reference_information_extracted_multiple instead."
            )
            reference_information_extracted_multiple = _merge_param(
                reference_information_extracted, reference_information_extracted_multiple
            )
        kwargs.update(
            {
                "reference_image_multiple": reference_image_multiple,
                "reference_strength_multiple": reference_strength_multiple,
                "reference_information_extracted_multiple": reference_information_extracted_multiple,
            }
        )
        kwargs.update(
            {
                "image": image,
                "strength": strength,
                "noise": noise,
            }
        )
        if decrisp_mode:
            kwargs.update({"dynamic_thresholding": True})
        if variety_boost:
            kwargs.update({"skip_cfg_above_sigma": 19})
        # 清理空值
        param = {k: v for k, v in kwargs.items() if v is not None}
        _build_prop = Params(**param)
        assert _build_prop, "Params validate failed"
        return cls(
            input=prompt,
            model=model,
            action=action,
            parameters=_build_prop
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
                _log_data.get("parameters", {}).update({
                    "image": "base64 data" if self.parameters.image else None,
                    "mask": "base64 data" if self.parameters.mask else None,
                    "reference_image_multiple": ["base64 data"] * len(
                        self.parameters.reference_image_multiple) if self.parameters.reference_image_multiple else None,
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
                raise SessionHttpError("An AsyncSession RequestsError occurred, maybe SSL error. Try again later!")
            except httpx.HTTPError as exc:
                logger.exception(exc)
                raise SessionHttpError("An HTTPError occurred, maybe SSL error. Try again later!")
            except APIError as e:
                raise e
            except Exception as e:
                logger.opt(exception=e).exception("An Unexpected error occurred")
                raise e
