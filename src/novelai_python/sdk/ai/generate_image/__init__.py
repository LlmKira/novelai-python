# -*- coding: utf-8 -*-
# @Author  : sudoskys
# @File    : __init__.py

import json
import math
import re
from copy import deepcopy
from enum import Enum
from io import BytesIO
from typing import Optional, Union, List
from zipfile import ZipFile, BadZipFile

import curl_cffi
import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import ConfigDict, PrivateAttr, model_validator, Field
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception
from typing_extensions import override

from novelai_python.sdk.ai._cost import CostCalculator
from novelai_python.sdk.ai._enum import Model, Sampler, NoiseSchedule, Action, UCPreset, \
    INPAINTING_MODEL_LIST, get_default_uc_preset, \
    ModelTypeAlias, UCPresetTypeAlias, get_default_noise_schedule, get_supported_noise_schedule, \
    get_model_group, ModelGroups, get_supported_params, get_modifiers
from .params import Params, get_default_params
from .schema import Character, V4Prompt, V4NegativePrompt, PositionMap
from ...schema import ApiBaseModel
from ...._exceptions import APIError, AuthError, ConcurrentGenerationError, SessionHttpError, DataSerializationError
from ...._response.ai.generate_image import ImageGenerateResp, RequestParams
from ....credential import CredentialBase
from ....utils import try_jsonfy


class GenerateImageInfer(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    """Endpoint"""

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    _mutual_exclusion: bool = PrivateAttr(False)
    """Positive words and negative words are mutually exclusive, and conflicting negative words are deleted first."""

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

    input: str = "1girl, best quality, amazing quality, very aesthetic, absurdres"
    model: ModelTypeAlias = "nai-diffusion-3"
    action: Union[str, Action] = Field(Action.GENERATE, description="Mode for img generate")
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

            # Lowres means we don't found any negative prompt.
            # If the default negative prompt is lowres, and the user has set a negative prompt,
            # then the default negative prompt is not added.
            if self.parameters.negative_prompt and default_negative_prompt == "lowres":
                default_negative_prompt = ""

            # Combine the negative prompt preset and the user's negative prompt
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

        if self.parameters.qualityToggle:
            logger.trace("Enhancing input with qualityToggle, will modify input prompt.")
            self.input = enhance_message(self.input)

        if self._mutual_exclusion:
            logger.trace("Mutual exclusion is enabled, will modify negative prompt.")
            input_prompt = {x.strip(): x for x in self.input.split(",")}
            uc_prompt = {x.strip(): x for x in self.parameters.negative_prompt.split(",")}
            # Remove conflicting negative words
            for key in input_prompt:
                if key in uc_prompt:
                    uc_prompt.pop(key)
            self.parameters.negative_prompt = ",".join(uc_prompt.values()).strip()
            
        # Instantly remove nsfw if input contains it
        elif "nsfw" in self.input and "nsfw" in self.parameters.negative_prompt:
            uc_prompt = {x.strip(): x for x in self.parameters.negative_prompt.split(",")}
            uc_prompt.pop("nsfw", None)
            
            self.parameters.negative_prompt = ",".join(uc_prompt.values()).strip()

    @model_validator(mode="after")
    def _build_nai4_prompt(self):
        """
        Build V4Prompt and V4NegativePrompt from character prompts.
        :return: self
        """
        if get_supported_params(self.model).v4_0legacyUC:
            self.parameters.legacy_uc = get_supported_params(self.model).v4_0legacyUC
        if get_supported_params(self.model).v4Prompts:
            if self.parameters.v4_prompt is None:
                # Remove furry tag from base caption
                base_caption = self.input
                if get_supported_params(self.model).hasFurryMode:
                    if base_caption.startswith("fur dataset, "):
                        base_caption = base_caption.replace("fur dataset, ", "")
                self.parameters.v4_prompt = V4Prompt.build_from_character_prompts(
                    base_caption=base_caption,
                    character_prompts=self.parameters.characterPrompts
                )
            if self.parameters.v4_negative_prompt is None:
                self.parameters.v4_negative_prompt = V4NegativePrompt.build_from_character_prompts(
                    negative_prompt=self.parameters.negative_prompt,
                    character_prompts=self.parameters.characterPrompts,
                    legacy_uc=self.parameters.legacy_uc
                )
        if not get_supported_params(self.model).vibetransfer:
            if self.parameters.reference_image_multiple:
                logger.warning("Vibe transfer is not supported for this model.")
            self.parameters.reference_image_multiple = None # Auto exclude None values
            self.parameters.reference_information_extracted_multiple = None # Auto exclude None values
            self.parameters.reference_strength_multiple = None # Auto exclude None values

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
        if self.parameters.characterPrompts:
            self.parameters.use_coords = any([c.center != PositionMap.AUTO for c in self.parameters.characterPrompts])
            
            if get_supported_params(self.model).v4Prompts and self.parameters.v4_prompt is not None:
                self.parameters.v4_prompt.use_coords = self.parameters.use_coords
        # Mix Prompt Warning
        if self.input.count('|') > 6:
            logger.warning("Maximum prompt mixes exceeded. Extra will be ignored.")

        # Remove the image if the model does not support it
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
            logger.warning("sm_dyn is disabled when sm is disabled.")
            self.parameters.sm_dyn = False

        # DDIM DON'T SUPPORT sm and sm_dyn
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

        # Remove noise_schedule and cfg_rescale if not supported
        if not get_supported_params(self.model).noiseSchedule:
            self.parameters.cfg_rescale = None
            self.parameters.noise_schedule = None

        if (self.model in INPAINTING_MODEL_LIST) and (self.parameters.sampler in [Sampler.DDIM, Sampler.DDIM_V3]):
            self.parameters.sampler = Sampler.K_EULER_ANCESTRAL

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

        if not get_supported_params(self.model).dynamicThresholding:
            self.parameters.dynamic_thresholding = False

        if self.model == Model.CUSTOM and self.action == Action.INFILL:
            self.endpoint = "http://custom-exposed-full-inpaint-anime-v4-staging.ai.svc.cluster.local/"

        # == Noise Schedule ==
        if self.parameters.noise_schedule is None:
            self.parameters.noise_schedule = get_default_noise_schedule(self.parameters.sampler)
        supported_noise_schedule = get_supported_noise_schedule(sample_type=self.parameters.sampler, model=self.model)
        if supported_noise_schedule:
            if self.parameters.noise_schedule not in supported_noise_schedule:
                raise ValueError(f"Invalid noise_schedule, must be one of {supported_noise_schedule}")
        else:
            logger.warning(f"Inactive sampler {self.parameters.sampler} does not support noise_schedule.")

        # == Action ==
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
        # == Color Correction ==
        if self.action == Action.IMG2IMG:
            self.parameters.color_correct = True

        if get_supported_params(self.model).img2imgInpainting and self.parameters.mask and self.parameters.inpaintImg2ImgStrength != 1:
            self.parameters.color_correct = True

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
            negative_prompt: str = None,
            ucPreset: UCPresetTypeAlias = None,
            sm: bool = None,
            steps: int = None,
            seed: int = None,
            sampler: Union[Sampler, str] = None,
            width: int = None,
            height: int = None,
            add_original_image: bool = None,
            character_prompts: List[Character] = None,
            reference_image_multiple: List[Union[str, bytes]] = None,
            reference_strength_multiple: List[float] = None,
            reference_information_extracted_multiple: List[float] = None,
            qualityToggle: bool = None,
            decrisp_mode: bool = None,
            variety_boost: bool = None,
            furry_mode: bool = None,
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
        :param furry_mode: Whether to use furry mode.
        :return:
        """
        # Get default parameters for the model
        params = get_default_params(model)

        # Update only explicitly set parameters
        if negative_prompt is not None:
            params.negative_prompt = negative_prompt
        if ucPreset is not None:
            params.ucPreset = ucPreset
        if sm is not None:
            params.sm = sm
        if steps is not None:
            params.steps = steps
        if seed is not None:
            params.seed = seed
        if sampler is not None:
            params.sampler = sampler
        if width is not None:
            params.width = width
        if height is not None:
            params.height = height
        if add_original_image is not None:
            params.add_original_image = add_original_image
        if character_prompts is not None:
            params.characterPrompts = character_prompts
        if reference_image_multiple is not None:
            params.reference_image_multiple = reference_image_multiple
        if reference_strength_multiple is not None:
            params.reference_strength_multiple = reference_strength_multiple
        if reference_information_extracted_multiple is not None:
            params.reference_information_extracted_multiple = reference_information_extracted_multiple
        if qualityToggle is not None:
            params.qualityToggle = qualityToggle
        if decrisp_mode is not None:
            params.dynamic_thresholding = decrisp_mode
        if variety_boost is not None:
            params.skip_cfg_above_sigma = get_supported_params(model).cfgDelaySigma if variety_boost else None
        if furry_mode is True:
            prompt = f"fur dataset, {prompt}"
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
            model: Union[Model, str] = Model.NAI_DIFFUSION_4_5_FULL,
            image: Union[bytes, str],
            strength: float = None,
            noise: float = None,
            seed: int = None,
            extra_noise_seed: int = None,
            negative_prompt: str = None,
            ucPreset: UCPresetTypeAlias = None,
            steps: int = None,
            sampler: Union[Sampler, str] = None,
            width: int = None,
            height: int = None,
            add_original_image: bool = None,
            character_prompts: List[Character] = None,
            reference_image_multiple: List[Union[str, bytes]] = None,
            reference_strength_multiple: List[float] = None,
            reference_information_extracted_multiple: List[float] = None,
            qualityToggle: bool = None,
            decrisp_mode: bool = None,
            variety_boost: bool = None
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
        :param model: Model for generation, which NOT end with 'inpainting'.
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
        # Get default parameters for the model
        params = get_default_params(model)

        # Update only explicitly set parameters
        params.image = image  # image is required for img2img
        if strength is not None:
            params.strength = strength
        if noise is not None:
            params.noise = noise
        if seed is not None:
            params.seed = seed
        if extra_noise_seed is not None:
            params.extra_noise_seed = extra_noise_seed
        if negative_prompt is not None:
            params.negative_prompt = negative_prompt
        if ucPreset is not None:
            params.ucPreset = ucPreset
        if steps is not None:
            params.steps = steps
        if sampler is not None:
            params.sampler = sampler
        if width is not None:
            params.width = width
        if height is not None:
            params.height = height
        if add_original_image is not None:
            params.add_original_image = add_original_image
        if character_prompts is not None:
            params.characterPrompts = character_prompts
        if reference_image_multiple is not None:
            params.reference_image_multiple = reference_image_multiple
        if reference_strength_multiple is not None:
            params.reference_strength_multiple = reference_strength_multiple
        if reference_information_extracted_multiple is not None:
            params.reference_information_extracted_multiple = reference_information_extracted_multiple
        if qualityToggle is not None:
            params.qualityToggle = qualityToggle
        if decrisp_mode is not None:
            params.dynamic_thresholding = decrisp_mode
        if variety_boost is not None:
            params.skip_cfg_above_sigma = 19 if variety_boost else None

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
            model: Union[Model, str],
            image: Union[bytes, str],
            mask: Union[bytes, str],
            strength: float = None,
            negative_prompt: str = None,
            ucPreset: UCPresetTypeAlias = None,
            steps: int = None,
            seed: int = None,
            sampler: Union[Sampler, str] = None,
            width: int = None,
            height: int = None,
            add_original_image: bool = None,
            character_prompts: List[Character] = None,
            reference_image_multiple: List[Union[str, bytes]] = None,
            reference_strength_multiple: List[float] = None,
            reference_information_extracted_multiple: List[float] = None,
            qualityToggle: bool = None,
            decrisp_mode: bool = None,
            variety_boost: bool = None,
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
        # Get default parameters for the model
        params = get_default_params(model)

        # Update only explicitly set parameters
        params.image = image  # image is required for infill
        params.mask = mask  # mask is required for infill
        if strength is not None:
            params.strength = strength
        if negative_prompt is not None:
            params.negative_prompt = negative_prompt
        if ucPreset is not None:
            params.ucPreset = ucPreset
        if steps is not None:
            params.steps = steps
        if seed is not None:
            params.seed = seed
        if sampler is not None:
            params.sampler = sampler
        if width is not None:
            params.width = width
        if height is not None:
            params.height = height
        if add_original_image is not None:
            params.add_original_image = add_original_image
        if character_prompts is not None:
            params.characterPrompts = character_prompts
        if reference_image_multiple is not None:
            params.reference_image_multiple = reference_image_multiple
        if reference_strength_multiple is not None:
            params.reference_strength_multiple = reference_strength_multiple
        if reference_information_extracted_multiple is not None:
            params.reference_information_extracted_multiple = reference_information_extracted_multiple
        if qualityToggle is not None:
            params.qualityToggle = qualityToggle
        if decrisp_mode is not None:
            params.dynamic_thresholding = decrisp_mode
        if variety_boost is not None:
            params.skip_cfg_above_sigma = get_supported_params(model).cfgDelaySigma if variety_boost else None

        return GenerateImageInfer(
            input=prompt,
            model=model,
            action=Action.INFILL,
            parameters=params
        )

    @retry(
        wait=wait_random(min=1, max=3),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(lambda e: hasattr(e, "code") and str(e.code) == "500"),
        reraise=True
    )
    async def request(
            self,
            session: Union[AsyncSession, "CredentialBase"],
            *,
            override_headers: Optional[dict] = None,
    ) -> ImageGenerateResp:
        """
        **Generate images using NovelAI's diffusion models.**

        According to our Terms of Service, all generation requests must be initiated by a human action. Automating text
        or image generation to create excessive load on our systems is not allowed.

        :param override_headers: Headers to override the default headers.
        :param session: Async session object or credential-based session.
        :return: ImageGenerateResp containing the response data and metadata.
        :raises AuthError: If the request is unauthorized.
        :raises APIError: If the API returns an error.
        :raises ConcurrentGenerationError: If the request is rate-limited.
        :raises SessionHttpError: If an HTTP error occurs.
        :raises DataSerializationError: If an error occurs while processing the response data.
        """
        # Prepare request data
        request_data = self.model_dump(mode="json", exclude_none=True)
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)

            # Log the request data (sanitize sensitive content)
            try:
                _log_data = deepcopy(request_data)
                if self.parameters.image:
                    _log_data["parameters"]["image"] = "base64 data hidden"
                if self.parameters.mask:
                    _log_data["parameters"]["mask"] = "base64 data hidden"
                if self.parameters.reference_image_multiple:
                    _log_data["parameters"]["reference_image_multiple"] = ["base64 data hidden"] * len(
                        self.parameters.reference_image_multiple
                    )
                logger.debug(f"Request Data: {json.dumps(_log_data, indent=2)}")
            except Exception as e:
                logger.warning(f"Failed to log request data: {e}")

            # Perform request and handle response
            try:
                self.ensure_session_has_post_method(sess)
                response = await sess.post(
                    self.base_url,
                    data=json.dumps(request_data).encode("utf-8"),
                )
                # Validate response content type and status code
                if (
                        response.headers.get("Content-Type")
                        not in ["binary/octet-stream", "application/x-zip-compressed"]
                        or response.status_code >= 400
                ):
                    error_message = await self.handle_error_response(response, request_data)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400, 401, 402]:
                        # 400 : validation error
                        # 401 : unauthorized
                        # 402 : payment required
                        # 409 : conflict
                        raise AuthError(message, request=request_data, code=status_code, response=error_message)
                    elif status_code == 409:
                        raise APIError(message, request=request_data, code=status_code, response=error_message)
                    elif status_code == 429:
                        raise ConcurrentGenerationError(
                            message=message,
                            request=request_data,
                            code=status_code,
                            response=error_message,
                        )
                    else:
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
                    return ImageGenerateResp(
                        meta=RequestParams(
                            endpoint=self.base_url,
                            raw_request=request_data,
                        ),
                        files=unzip_content,
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
                raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.")
            except httpx.HTTPError as exc:
                logger.exception(exc)
                raise SessionHttpError("An HTTP error occurred. Try again later.")
            except APIError as e:
                raise e
            except Exception as e:
                logger.opt(exception=e).exception("Unexpected error occurred during the request.")
                raise Exception("An unexpected error occurred.") from e
