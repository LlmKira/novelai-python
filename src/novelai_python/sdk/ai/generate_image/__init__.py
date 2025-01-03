# -*- coding: utf-8 -*-
# @Author  : sudoskys
# @File    : __init__.py

import base64
import json
import math
import random
import re
from copy import deepcopy
from enum import Enum
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
    INPAINTING_MODEL_LIST, get_default_uc_preset, \
    ModelTypeAlias, UCPresetTypeAlias, get_default_noise_schedule, get_supported_noise_schedule, \
    get_model_group, ModelGroups, get_supported_params, get_modifiers, ImageBytesTypeAlias
from .schema import Character, V4Prompt, V4NegativePrompt, PositionMap
from ...schema import ApiBaseModel
from ...._exceptions import APIError, AuthError, ConcurrentGenerationError, SessionHttpError
from ...._response.ai.generate_image import ImageGenerateResp, RequestParams
from ....credential import CredentialBase
from ....utils import try_jsonfy


def is_multiple_of_01(num, precision=1e-10):
    remainder = num % 0.01
    return abs(remainder) < precision or abs(0.01 - remainder) < precision


class Params(BaseModel):
    width: int = Field(832, ge=64, le=49152)
    """Width For Image"""
    height: int = Field(1216, ge=64, le=49152)
    """Height For Image"""
    scale: float = Field(6.0, ge=0, le=10, multiple_of=0.1)
    """Prompt Guidance"""
    sampler: Sampler = Sampler.K_EULER_ANCESTRAL
    """Sampler For Generate Image"""
    steps: int = Field(23, ge=1, le=50)
    """Steps"""
    n_samples: int = Field(1, ge=1, le=8)
    """Number of samples"""
    strength: Optional[float] = Field(0.7, ge=0.01, le=0.99, multiple_of=0.01)
    """Strength for img2img"""
    noise: Optional[float] = Field(0, ge=0, le=0.99, multiple_of=0.01)
    """Noise for img2img"""
    ucPreset: UCPresetTypeAlias = Field(None, ge=0)
    """The Negative Prompt Preset, Bigger or equal to 0"""
    qualityToggle: bool = True
    """Whether to add the quality prompt"""
    sm: Optional[bool] = False
    # TODO: find out the usage
    sm_dyn: Optional[bool] = False
    # TODO: find out the usage
    dynamic_thresholding: bool = False
    """Decrisp:Reduce artifacts caused by high prompt guidance values"""
    controlnet_strength: float = Field(1.0, ge=0.1, le=2, multiple_of=0.1)
    """ControlNet Strength"""
    legacy: bool = False
    """Legacy Mode"""
    cfg_rescale: Optional[float] = Field(0, ge=0, le=1, multiple_of=0.02)
    """Prompt Guidance Rescale"""
    noise_schedule: Optional[NoiseSchedule] = None
    """Noise Schedule"""
    legacy_v3_extend: Optional[bool] = False
    """Legacy V3 Extend"""
    mask: ImageBytesTypeAlias = None
    """Mask for Inpainting"""
    seed: int = Field(
        default_factory=lambda: random.randint(0, 4294967295 - 7),
        gt=0,
        le=4294967295 - 7,
    )
    """Seed"""
    image: ImageBytesTypeAlias = None
    """Image for img2img"""
    negative_prompt: Optional[str] = ''
    """Negative Prompt"""
    reference_image_multiple: Optional[List[Union[str, bytes]]] = Field(default_factory=list)
    """Reference Image For Vibe Mode"""
    reference_information_extracted_multiple: Optional[List[float]] = Field(default_factory=list)
    """Reference Information Extracted For Vibe Mode"""
    reference_strength_multiple: Optional[List[float]] = Field(
        default=list,
        description="Reference Strength For Vibe Mode"
    )
    """Reference Strength For Vibe Mode"""
    extra_noise_seed: Optional[int] = Field(None, gt=0, le=4294967295 - 7)
    """Extra Noise Seed"""

    # ====Version3 ====
    params_version: int = 3
    """Params Version For Request"""
    add_original_image: Optional[bool] = Field(False, description="Overlay Original Image")
    """
    Overlay Original Image.Prevents the existing image from changing,
    but can introduce seams along the edge of the mask.
    """
    use_coords: bool = Field(False, description="Use Coordinates")
    """Use Coordinates"""
    characterPrompts: List[Character] = Field(default_factory=list)
    """Character Prompts"""

    v4_prompt: Optional[V4Prompt] = Field(None, description="V4 Prompt")
    """V4 Prompt"""
    v4_negative_prompt: Optional[V4NegativePrompt] = Field(None, description="V4 Negative Prompt")
    """V4 Negative Prompt"""

    deliberate_euler_ancestral_bug: Optional[bool] = Field(False, description="Deliberate Euler Ancestral Bug")
    """Deliberate Euler Ancestral Bug"""
    prefer_brownian: bool = Field(True, description="Prefer Brownian")
    """Prefer Brownian"""

    # ======== V1 ========
    controlnet_condition: Optional[str] = None
    """ControlNet Condition"""
    controlnet_model: Optional[ControlNetModel] = None
    """ControlNet Model"""
    skip_cfg_above_sigma: Optional[int] = None
    """Variety Boost, a new feature to improve the diversity of samples."""
    uncond_scale: Optional[float] = Field(None, ge=0, le=1.5, multiple_of=0.05)
    """Undesired Content Strength"""

    @model_validator(mode="after")
    def v_character(self):
        if len(self.characterPrompts) > 6:
            raise ValueError("Too many character given")
        return self

    @field_validator('uncond_scale')
    def v_uncond_scale(cls, v: float):
        """
        Align
        :param v:
        :return: fixed value
        """
        if v == 0:
            v = 0.00001
        return v

    @field_validator('width')
    def v_width(cls, v: int):
        """
        Must be multiple of 64
        :param v:
        :return: fixed value
        """
        if v % 64 != 0:
            raise ValueError("Invalid width, must be multiple of 64.")
        return v

    @field_validator('height')
    def v_height(cls, v: int):
        """
        Must be multiple of 64
        :param v:
        :return: fixed value
        """
        if v % 64 != 0:
            raise ValueError("Invalid height, must be multiple of 64.")
        return v

    @model_validator(mode="after")
    def _build_image(self):
        # == Mask ==
        if self.mask is not None:
            if isinstance(self.mask, str) and self.mask.startswith("data:"):
                raise ValueError(
                    "Invalid `mask` format, must be base64 encoded directly, "
                    "you can also provide bytes directly."
                )
            if isinstance(self.mask, bytes):
                self.mask = base64.b64encode(self.mask).decode("utf-8")

        # == Image ==
        if self.image is not None:
            if isinstance(self.image, str) and self.image.startswith("data:"):
                raise ValueError(
                    "Invalid `image` format, must be base64 encoded directly, "
                    "you can also provide bytes directly."
                )
            if isinstance(self.image, bytes):
                self.image = base64.b64encode(self.image).decode("utf-8")
            self.image = self.resize_image(
                self.image,
                self.width,
                self.height
            )
        return self

    @model_validator(mode="after")
    def _build_reference_image(self):
        # Resize the image to the specified size
        if self.reference_image_multiple is not None:
            new_images = []
            for reference_image in self.reference_image_multiple:
                if isinstance(reference_image, str):
                    if reference_image.startswith("data:"):
                        raise ValueError("Invalid `reference_image` format, must be base64 encoded directly.")
                    new_images.append(reference_image)
                elif isinstance(reference_image, bytes):
                    new_image = self.add_image_to_black_background(
                        reference_image,
                        target_size=(448, 448),
                        transparency=True
                    )
                    if isinstance(new_image, bytes):
                        new_image = base64.b64encode(new_image).decode("utf-8")
                    new_images.append(new_image)
                else:
                    raise ValueError("Invalid `reference_image` format, must be base64 encoded directly.")
            self.reference_image_multiple = new_images
        # 如果都不是 None 时，比较他们的长度
        if all([
            self.reference_strength_multiple,
            self.reference_image_multiple,
            self.reference_information_extracted_multiple
        ]):
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
        return self

    @field_validator('reference_strength_multiple')
    def v_reference_strength_multiple(cls, v):
        # Field(0.6,ge=0,le=1,multiple_of=0.01,description="the stronger the AI will try to emulate visual cues.")
        if v is None:
            return v
        for i in v:
            if not 0 <= i <= 1:
                raise ValueError("Invalid reference_strength_multiple, must be in [0, 1].")
            if not is_multiple_of_01(i):
                raise ValueError("Invalid reference_strength_multiple item, must be multiple of 0.01.")
        return v

    @field_validator('reference_information_extracted_multiple')
    def v_reference_information_extracted_multiple(cls, v):
        # List[Field(..., ge=0, le=1, multiple_of=0.01)]
        if v is None:
            return v
        for i in v:
            if not 0 <= i <= 1:
                raise ValueError("Invalid reference_information_extracted_multiple, must be in [0, 1].")
            if not is_multiple_of_01(i):
                raise ValueError("Invalid reference_information_extracted_multiple item, must be multiple of 0.01.")
        return v

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


class GenerateImageInfer(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    _mutual_exclusion: bool = PrivateAttr(False)
    """Positive words and negative words are mutually exclusive, and conflicting negative words are deleted first."""
    _quality_modifier: bool = PrivateAttr(True)
    """Add Quality Modifier To Input"""

    def set_mutual_exclusion(self, value: bool):
        """
        **Enable This will modify the negative prompt.**
        Default is False.

        Positive words and negative words are mutually exclusive, and conflicting negative words are deleted first.
        :param value: bool
        :return: self
        """
        self._mutual_exclusion = bool(value)
        return self

    def set_quality_modifier(self, value: bool):
        """
        **Enable This will modify the input prompt.**
        Default is True.

        Add Quality Modifier To Input.
        Whether to add the quality vocabulary used by the web application.
        :param value:
        :return:
        """
        self._quality_modifier = bool(value)
        return self

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    action: Union[str, Action] = Field(Action.GENERATE, description="Mode for img generate")
    input: str = "1girl, best quality, amazing quality, very aesthetic, absurdres"
    model: ModelTypeAlias = "nai-diffusion-3"
    parameters: Union[Params]
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
            uc_preset = self.parameters.ucPreset
            # If ucPreset is Enum, get the value
            if isinstance(self.parameters.ucPreset, Enum):
                uc_preset = self.parameters.ucPreset.value
            default_negative_prompt = get_default_uc_preset(self.model, uc_preset)
            self.parameters.negative_prompt = ", ".join(
                filter(None, [default_negative_prompt, self.parameters.negative_prompt])
            )

        # Add quality prompt based on qualityToggle
        modifier = get_modifiers(self.model)
        quality_tags, suffix = modifier.qualityTags, modifier.suffix

        def enhance_text_part(_part, _quality_tags, _suffix):
            text_parts = _part.split(" Text:")
            enhanced_text_parts = [
                _quality_tags + text_part + _suffix + ('.' if _suffix and len(text_parts) > 1 else '')
                if index == 0
                else text_part
                for index, text_part in enumerate(text_parts)
            ]
            return " Text:".join(enhanced_text_parts)

        def enhance_simple_part(_part, _quality_tags, _suffix):
            match = re.search(r"(:[\d.]+$)", _part)
            matched_value = match.group(0) if match else None
            core_part = _part[:-len(matched_value)] if matched_value else _part
            return _quality_tags + core_part + _suffix + (matched_value or "")

        def enhance_message(_prompt):
            try:
                if get_supported_params(self.model).characterPrompts:
                    parts = _prompt.split("|")
                    enhanced_parts = [
                        quality_tags + part + suffix
                        if index == 0 and not get_supported_params(self.model).text
                        else enhance_text_part(part, quality_tags, suffix)
                        if index == 0
                        else part
                        for index, part in enumerate(parts)
                    ]
                    return "|".join(enhanced_parts)
                else:
                    parts = _prompt.split("|")
                    enhanced_parts = [
                        enhance_simple_part(part, quality_tags, suffix)
                        for part in parts
                    ]
                    return "|".join(enhanced_parts)
            except Exception as e:
                logger.error(
                    f"Failed to enhance `{_prompt}` because {e},"
                    f"Report this issue to https://github.com/LLMKIRA/novelai-python/issues"
                )
                return _prompt

        if self._quality_modifier:
            logger.trace("Enhancing input with quality modifier, will modify input prompt.")
            self.input = enhance_message(self.input)

        if self._mutual_exclusion:
            logger.trace("Mutual exclusion is enabled, will modify negative prompt.")
            input_prompt = {x.strip(): x for x in self.input.split(",")}
            uc_prompt = {x.strip(): x for x in self.parameters.negative_prompt.split(",")}
            # Remove conflicting negative words
            for key in input_prompt:
                if key in uc_prompt:
                    uc_prompt.pop(key)
            self.parameters.negative_prompt = ",".join(uc_prompt.values())

    @model_validator(mode="after")
    def _build_nai4_prompt(self):
        """
        Build V4Prompt and V4NegativePrompt from character prompts.
        :return: self
        """
        if get_supported_params(self.model).v4Prompts:
            if self.parameters.v4_prompt is None:
                self.parameters.v4_prompt = V4Prompt.build_from_character_prompts(
                    prompt=self.input,
                    character_prompts=self.parameters.characterPrompts
                )
            if self.parameters.v4_negative_prompt is None:
                self.parameters.v4_negative_prompt = V4NegativePrompt.build_from_character_prompts(
                    negative_prompt=self.parameters.negative_prompt,
                    character_prompts=self.parameters.characterPrompts
                )
        if not get_supported_params(self.model).vibetransfer:
            if self.parameters.reference_image_multiple:
                logger.warning("Vibe transfer is not supported for this model.")
            self.parameters.reference_image_multiple = []
            self.parameters.reference_information_extracted_multiple = []
            self.parameters.reference_strength_multiple = []

        if not get_supported_params(self.model).controlnet:
            if self.parameters.controlnet_condition is not None:
                logger.warning("ControlNet is not supported for this model.")
                self.parameters.controlnet_condition = None
            if self.parameters.controlnet_model is not None:
                logger.warning("ControlNet is not supported for this model.")
                self.parameters.controlnet_model = None
        return self

    @model_validator(mode="after")
    def _backend_logic(self):
        """
        Calibration results.

        **NOTE: It is forbidden to write logic that does not belong to novelai.net here**
        :return: self
        """
        if self.action == Action.GENERATE:
            if self.parameters.image is not None:
                raise ValueError("You are using generate action, image is not required for non-generate mode.")
            if self.parameters.mask is not None:
                raise ValueError("You are using generate action, mask is not required for non-generate mode.")

        if self.action == Action.INFILL:
            if self.model not in INPAINTING_MODEL_LIST:
                raise ValueError(f"You must use {INPAINTING_MODEL_LIST}")
            if not self.parameters.mask:
                logger.warning("Mask maybe required for infill mode!")

        if self.action == Action.IMG2IMG:
            if self.parameters.extra_noise_seed is None:
                self.parameters.extra_noise_seed = self.parameters.seed

        if self.action == Action.IMG2IMG:
            if self.parameters.sm_dyn is True:
                logger.warning("sm_dyn be disabled when sm in Img2Img mode.")
            if self.parameters.sm is True:
                logger.warning("sm be disabled when sm_dyn in Img2Img mode.")
            self.parameters.sm = False
            self.parameters.sm_dyn = False
            if self.parameters.image is None:
                raise ValueError("image is must required for img2img mode.")

        # Check Image
        if self.parameters.image is None:
            self.parameters.strength = None
            self.parameters.noise = None

        # == Sampler ==
        if self.parameters.sampler in [Sampler.NAI_SMEA]:
            self.parameters.sm = True
            self.parameters.sampler = Sampler.K_EULER_ANCESTRAL

        if self.parameters.sampler in [Sampler.NAI_SMEA_DYN]:
            if not self.parameters.sm_dyn:
                logger.warning("sm and sm_dyn is enabled when using nai_smea_dyn sampler.")
            self.parameters.sampler = Sampler.K_EULER_ANCESTRAL
            self.parameters.sm = True
            self.parameters.sm_dyn = True

        if self.parameters.sm_dyn and (not self.parameters.sm):
            self.parameters.sm = True

        # AUTO SMEA SETTING
        """
        def sm_size_cast(model: Model):
            if model in [
                Model.NAI_DIFFUSION_V3,
                Model.NAI_DIFFUSION_V3_INPAINTING,
                Model.NAI_DIFFUSION_FURRY_V3,
                Model.NAI_DIFFUSION_FURRY_V3_INPAINTING,
                Model.CUSTOM
            ]:
                return 2166785
            return 1064961
        if self.parameters.autoSmea and (self.parameters.width * self.parameters.height < sm_size_cast(self.model)):
            self.parameters.autoSmea = False
        """

        if self.parameters.characterPrompts:
            self.parameters.use_coords = any([c.center != PositionMap.AUTO for c in self.parameters.characterPrompts])

        # Mix Prompt Warning
        if self.input.count('|') > 6:
            logger.warning("Maximum prompt mixes exceeded. Extra will be ignored.")

        if self.parameters.sampler in [
            Sampler.DDIM,
            Sampler.DDIM_V3
        ]:
            if self.parameters.sm_dyn or self.parameters.sm:
                logger.warning("sm and sm_dyn is disabled when using ddim sampler.")
            self.parameters.sm = False
            self.parameters.sm_dyn = False

        if self.action != Action.INFILL:
            self.parameters.mask = None

        if self.parameters.uncond_scale == 0:
            self.parameters.uncond_scale = 0.00001

        if get_model_group(self.model) == ModelGroups.STABLE_DIFFUSION:
            self.parameters.uncond_scale = None

        if not get_supported_params(self.model).noiseSchedule:
            self.parameters.noise_schedule = None
            self.parameters.cfg_rescale = None

        if (self.model in INPAINTING_MODEL_LIST) and (self.parameters.sampler in [Sampler.DDIM, Sampler.DDIM_V3]):
            self.parameters.sampler = Sampler.K_EULER_ANCESTRAL

        if self.parameters.sampler in [
            Sampler.DDIM,
            Sampler.PLMS,
            Sampler.K_LMS,
            Sampler.NAI_SMEA,
            Sampler.NAI_SMEA_DYN,
            Sampler.DDIM_V3,
            Sampler.K_DPM_FAST
        ]:
            self.parameters.noise_schedule = None

        if self.parameters.sampler == Sampler.K_EULER_ANCESTRAL and self.parameters.noise_schedule != NoiseSchedule.NATIVE:
            self.parameters.deliberate_euler_ancestral_bug = False
            self.parameters.prefer_brownian = True

        if self.parameters.skip_cfg_above_sigma is not None:
            scale_divisor, weight = (1, 3) if self.model == Model.DALLE_MINI else (8, 4)
            dimensions_scaled = [
                math.floor(self.parameters.width) / scale_divisor,
                math.floor(self.parameters.height) / scale_divisor
            ]
            # 初始化参考值 reference_value，用于标准化计算动态系数
            reference_value = 4 * math.floor(104) * math.floor(152)
            # 计算动态系数 dynamic_factor 并用于调整 skip_cfg_above_sigma
            dynamic_factor = ((weight * dimensions_scaled[0] * dimensions_scaled[1]) / reference_value) ** 0.5
            self.parameters.skip_cfg_above_sigma *= dynamic_factor
            self.parameters.skip_cfg_above_sigma = math.ceil(self.parameters.skip_cfg_above_sigma)

        if not get_supported_params(self.model).cfgDelay:
            self.parameters.skip_cfg_above_sigma = None

        if not get_supported_params(self.model).smea:
            self.parameters.sm = None
            self.parameters.sm_dyn = None

        # == Noise Schedule ==
        if self.parameters.noise_schedule is None:
            self.parameters.noise_schedule = get_default_noise_schedule(self.parameters.sampler)
        supported_noise_schedule = get_supported_noise_schedule(self.parameters.sampler)
        if supported_noise_schedule:
            if self.parameters.noise_schedule not in supported_noise_schedule:
                raise ValueError(f"Invalid noise_schedule, must be one of {supported_noise_schedule}")
        else:
            logger.warning(f"Inactive sampler {self.parameters.sampler} does not support noise_schedule.")

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
                image=bool(self.parameters.image),
                n_samples=self.parameters.n_samples,
                account_tier=3 if is_opus else 1,
                strength=self.parameters.strength,
                sampler=self.parameters.sampler,
                is_sm_enabled=bool(self.parameters.sm),
                is_sm_dynamic=bool(self.parameters.sm_dyn),
                is_account_active=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to calculate cost") from e

    @staticmethod
    def build_generate(
            prompt: str,
            *,
            model: Union[Model, str],
            negative_prompt: str = "",
            ucPreset: UCPresetTypeAlias = UCPreset.TYPE0,
            sm: bool = False,
            steps: int = 23,
            seed: int = None,
            sampler: Union[Sampler, str] = None,
            width: int = 832,
            height: int = 1216,
            add_original_image: bool = True,
            character_prompts: List[Character] = None,
            reference_image_multiple: List[Union[str, bytes]] = None,
            reference_strength_multiple: List[float] = None,
            reference_information_extracted_multiple: List[float] = None,
            qualityToggle: bool = False,
            decrisp_mode: bool = False,
            variety_boost: bool = False,
    ):
        """
        Quickly construct a parameter class that meets the requirements.

        If you need to define more parameters, you should initialize the Param class yourself.

        :param sm:
        :param reference_information_extracted_multiple:
        :param reference_strength_multiple:
        :param reference_image_multiple:
        :param prompt: Given prompt.
        :param model: Model for generation.
        :param negative_prompt: The things you don't want to see in the image.
        :param ucPreset: The negative prompt preset.
        :param steps: The steps for generation.
        :param seed: The seed for generation.
        :param sampler: The sampler for generation.
        :param width: The width of the image.
        :param height: The height of the image.
        :param add_original_image: Overlay Original Image. Prevents the existing image from changing,
                                    but can introduce seams along the edge of the mask.
        :param character_prompts: Character Prompts.
        :param qualityToggle: Use modifiers to make your images look more hentai.
        :param decrisp_mode: Reduce artifacts caused by high prompt guidance values.
        :param variety_boost: A new feature to improve the diversity of samples.
        :return:
        """
        if character_prompts is None:
            character_prompts = []
        if seed is None:
            seed = random.randint(0, 4294967295 - 7)
        if reference_strength_multiple is None:
            reference_image_multiple = []
        if reference_strength_multiple is None:
            reference_strength_multiple = []
        if reference_information_extracted_multiple is None:
            reference_information_extracted_multiple = []
        if len(reference_image_multiple) != len(reference_strength_multiple) != len(
                reference_information_extracted_multiple):
            raise ValueError("All three reference_* must be of equal length.")
        params = Params(
            width=width,
            height=height,
            sampler=sampler,
            characterPrompts=character_prompts,
            add_original_image=add_original_image,
            steps=steps,
            seed=seed,
            sm=sm,
            negative_prompt=negative_prompt,
            ucPreset=ucPreset,
            qualityToggle=qualityToggle,
            dynamic_thresholding=decrisp_mode,
            skip_cfg_above_sigma=19 if variety_boost else None,
            reference_image_multiple=reference_image_multiple,
            reference_information_extracted_multiple=reference_information_extracted_multiple,
            reference_strength_multiple=reference_strength_multiple,
        )
        return GenerateImageInfer(
            input=prompt,
            model=model,
            action=Action.GENERATE,
            parameters=params
        )

    @staticmethod
    def build_img2img(
            prompt: str,
            *,
            image: Union[bytes, str],
            strength: float = 0.7,
            noise: float = 0,
            seed: int = None,
            extra_noise_seed: int = None,
            model: Union[Model, str] = Model.NAI_DIFFUSION_3,
            negative_prompt: str = "",
            ucPreset: UCPresetTypeAlias = UCPreset.TYPE0,
            steps: int = 23,
            sampler: Union[Sampler, str] = None,
            width: int = 832,
            height: int = 1216,
            add_original_image: bool = True,
            character_prompts: List[Character] = None,
            reference_image_multiple: List[Union[str, bytes]] = None,
            reference_strength_multiple: List[float] = None,
            reference_information_extracted_multiple: List[float] = None,
            qualityToggle: bool = False,
            decrisp_mode: bool = False,
            variety_boost: bool = False
    ):
        """
        Quickly construct a parameter class that meets the requirements.

        If you need to define more parameters, you should initialize the Param class yourself.

        :param strength:
        :param image:
        :param noise: For image to image
        :param extra_noise_seed: Get extra_noise_seed
        :param reference_information_extracted_multiple:
        :param reference_strength_multiple:
        :param reference_image_multiple:
        :param prompt: Given prompt.
        :param model: Model for generation.
        :param negative_prompt: The things you don't want to see in the image.
        :param ucPreset: The negative prompt preset.
        :param steps: The steps for generation.
        :param seed: The seed for generation.
        :param sampler: The sampler for generation.
        :param width: The width of the image.
        :param height: The height of the image.
        :param add_original_image: Overlay Original Image. Prevents the existing image from changing,
                                    but can introduce seams along the edge of the mask.
        :param character_prompts: Character Prompts.
        :param qualityToggle: Use modifiers to make your images look more hentai.
        :param decrisp_mode: Reduce artifacts caused by high prompt guidance values.
        :param variety_boost: A new feature to improve the diversity of samples.
        :return:
        """
        if character_prompts is None:
            character_prompts = []
        if seed is None:
            seed = random.randint(0, 4294967295 - 7)
        if extra_noise_seed is None:
            extra_noise_seed = random.randint(0, 4294967295 - 7)
        if reference_strength_multiple is None:
            reference_image_multiple = []
        if reference_strength_multiple is None:
            reference_strength_multiple = []
        if reference_information_extracted_multiple is None:
            reference_information_extracted_multiple = []
        if len(reference_image_multiple) != len(reference_strength_multiple) != len(
                reference_information_extracted_multiple):
            raise ValueError("All three reference_* must be of equal length.")
        params = Params(
            image=image,
            strength=strength,
            noise=noise,
            width=width,
            height=height,
            sampler=sampler,
            characterPrompts=character_prompts,
            add_original_image=add_original_image,
            steps=steps,
            seed=seed,
            extra_noise_seed=extra_noise_seed,
            negative_prompt=negative_prompt,
            ucPreset=ucPreset,
            qualityToggle=qualityToggle,
            dynamic_thresholding=decrisp_mode,
            skip_cfg_above_sigma=19 if variety_boost else None,
            reference_image_multiple=reference_image_multiple,
            reference_information_extracted_multiple=reference_information_extracted_multiple,
            reference_strength_multiple=reference_strength_multiple,
        )
        return GenerateImageInfer(
            input=prompt,
            model=model,
            action=Action.IMG2IMG,
            parameters=params
        )

    @staticmethod
    def build_infill(
            prompt: str,
            *,
            image: Union[bytes, str],
            mask: Union[bytes, str],
            strength: float = 0.7,
            model: Union[Model, str] = Model.NAI_DIFFUSION_3,
            negative_prompt: str = "",
            ucPreset: UCPresetTypeAlias = UCPreset.TYPE0,
            steps: int = 23,
            seed: int = None,
            sampler: Union[Sampler, str] = None,
            width: int = 832,
            height: int = 1216,
            add_original_image: bool = True,
            character_prompts: List[Character] = None,
            reference_image_multiple: List[Union[str, bytes]] = None,
            reference_strength_multiple: List[float] = None,
            reference_information_extracted_multiple: List[float] = None,
            qualityToggle: bool = False,
            decrisp_mode: bool = False,
            variety_boost: bool = False,
    ):
        """
        Quickly construct a parameter class that meets the requirements.

        If you need to define more parameters, you should initialize the Param class yourself.

        :param strength: The strength
        :param mask: Given mask
        :param image: Given image
        :param reference_information_extracted_multiple:
        :param reference_strength_multiple:
        :param reference_image_multiple:
        :param prompt: Given prompt.
        :param model: Model for generation.
        :param negative_prompt: The things you don't want to see in the image.
        :param ucPreset: The negative prompt preset.
        :param steps: The steps for generation.
        :param seed: The seed for generation.
        :param sampler: The sampler for generation.
        :param width: The width of the image.
        :param height: The height of the image.
        :param add_original_image: Overlay Original Image. Prevents the existing image from changing,
                                    but can introduce seams along the edge of the mask.
        :param character_prompts: Character Prompts.
        :param qualityToggle: Use modifiers to make your images look more hentai.
        :param decrisp_mode: Reduce artifacts caused by high prompt guidance values.
        :param variety_boost: A new feature to improve the diversity of samples.
        :return:
        """
        if character_prompts is None:
            character_prompts = []
        if seed is None:
            seed = random.randint(0, 4294967295 - 7)
        if reference_strength_multiple is None:
            reference_image_multiple = []
        if reference_strength_multiple is None:
            reference_strength_multiple = []
        if reference_information_extracted_multiple is None:
            reference_information_extracted_multiple = []
        if len(reference_image_multiple) != len(reference_strength_multiple) != len(
                reference_information_extracted_multiple):
            raise ValueError("All three reference_* must be of equal length.")
        params = Params(
            width=width,
            height=height,
            sampler=sampler,
            image=image,
            mask=mask,
            strength=strength,
            characterPrompts=character_prompts,
            add_original_image=add_original_image,
            steps=steps,
            seed=seed,
            negative_prompt=negative_prompt,
            ucPreset=ucPreset,
            qualityToggle=qualityToggle,
            dynamic_thresholding=decrisp_mode,
            skip_cfg_above_sigma=19 if variety_boost else None,
            reference_image_multiple=reference_image_multiple,
            reference_information_extracted_multiple=reference_information_extracted_multiple,
            reference_strength_multiple=reference_strength_multiple,
        )
        return GenerateImageInfer(
            input=prompt,
            model=model,
            action=Action.INFILL,
            parameters=params
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
        **Generate images using NovelAI's diffusion models.**

        According to our Terms of Service, all generation requests must be initiated by a human action. Automating text or image generation to create excessive load on our systems is not allowed.

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
                if self.parameters.image:
                    _log_data["parameters"]["image"] = "base64 data"
                if self.parameters.mask:
                    _log_data["parameters"]["mask"] = "base64 data"
                if self.parameters.reference_image_multiple:
                    _log_data["parameters"]["reference_image_multiple"] = ["base64 data"] * len(
                        self.parameters.reference_image_multiple)
                logger.debug(f"Request Data: {json.dumps(_log_data, indent=2)}")
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
