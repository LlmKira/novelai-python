# @Author  : sudoskys
# @File    : __init__.py

import base64
import hashlib
import hmac
import json
import logging
import math
import os
import random
import re
import string
from collections.abc import AsyncIterator
from copy import deepcopy
from enum import Enum
from io import BytesIO
from typing import Union, override
from zipfile import BadZipFile, ZipFile

import curl_cffi
import msgpack
from curl_cffi.requests import AsyncSession
from pydantic import ConfigDict, Field, PrivateAttr, model_validator

from novelai_python._retry import retry_on_server_error
from novelai_python.sdk.ai._cost import CostCalculator
from novelai_python.sdk.ai._enum import (
    INPAINTING_MODEL_LIST,
    V5_MEDIUM_MODEL_LIST,
    Action,
    ImageFormat,
    Model,
    ModelGroups,
    ModelTypeAlias,
    NoiseSchedule,
    QualityPreset,
    Sampler,
    UCPresetTypeAlias,
    get_default_noise_schedule,
    get_default_uc_preset,
    get_max_characters,
    get_model_group,
    get_quality_suffix,
    get_supported_noise_schedule,
    get_supported_params,
    get_uc_preset_id,
    is_v5_model,
    supports_character_reference,
)
from novelai_python.sdk.ai._enum import (
    UCPreset as UCPreset,  # re-export
)
from novelai_python.sdk.ai._enum import (
    get_modifiers as get_modifiers,
)

from ...._exceptions import APIError, AuthError, ConcurrentGenerationError, DataSerializationError, SessionHttpError
from ...._response.ai.generate_image import ImageGenerateResp, ImageStreamEvent, RequestParams
from ....credential import CredentialBase
from ....utils import try_jsonfy
from ....utils.daily_limit import DailyImageLimiter, get_default_limiter
from ...schema import ApiBaseModel
from .params import Params, get_default_params
from .schema import Character, CharacterReference, PositionMap, V4NegativePrompt, V4Prompt
from .suggest_tags import SuggestTags as SuggestTags  # re-export

logger = logging.getLogger(__name__)

ZIP_CONTENT_TYPES = (
    "binary/octet-stream",
    "application/octet-stream",
    "application/x-zip-compressed",
    "application/zip",
)
IMAGE_CONTENT_TYPES = ("image/webp", "image/png", "image/jpeg")


def _sniff_image_extension(data: bytes) -> str | None:
    """Return the file extension when ``data`` is a bare image rather than a zip."""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    return None


def build_multipart_request(request_json: bytes, files: list[tuple[str, bytes]] | None = None) -> tuple[bytes, str]:
    """
    Wrap the request JSON the way the web client does for params_version >= 4:
    image parts first (``image/png``, filename ``blob``), then the JSON part ``request``.
    :param files: (part name, raw bytes) for every image the JSON references by part name.
    :return: (body, Content-Type header value)
    """
    boundary = "----WebKitFormBoundary" + "".join(random.choices(string.ascii_letters + string.digits, k=16))
    body = b""
    for name, data in files or []:
        body += (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; filename="blob"\r\n'
                f"Content-Type: image/png\r\n\r\n"
            ).encode()
            + data
            + b"\r\n"
        )
    body += (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="request"; filename="blob"\r\n'
            f"Content-Type: application/json\r\n\r\n"
        ).encode()
        + request_json
        + f"\r\n--{boundary}--\r\n".encode()
    )
    return body, f"multipart/form-data; boundary={boundary}"


# Per-process secret for image cache keys; the web client keys its cache the same way
# (HMAC-SHA256 of the base64 string with a random per-session key).
_IMAGE_CACHE_SECRET = os.urandom(32)


def _image_cache_key(b64: str) -> str:
    return hmac.new(_IMAGE_CACHE_SECRET, b64.encode("utf-8"), hashlib.sha256).hexdigest()


def split_image_parts(request_data: dict) -> list[tuple[str, bytes]]:
    """
    Move base64 images out of a multipart request into their own form parts, in place.

    The server reads every image field of a multipart request as the NAME of a form part
    ("image field references unknown form part" otherwise). Mirrors the web client
    (applyCacheTransformation + form building, 2026-10 bundle): ``image`` / ``mask`` /
    ``reference_image`` keep their key with the part name and get ``*_cache_secret_key``;
    ``reference_image_multiple`` / ``director_reference_images`` become ``*_cached`` lists of
    ``{cache_secret_key, data: <part name>}``. The image data is always sent, so the
    server-side cache is never relied on.
    :return: (part name, raw bytes) in the order the web client appends them.
    """
    params = request_data.get("parameters") or {}
    names: dict[str, str] = {}  # base64 -> part name; the same image is sent once

    def part(b64: str, name: str) -> str:
        return names.setdefault(b64, name)

    for key in ("image", "mask", "reference_image"):
        value = params.get(key)
        if isinstance(value, str) and value:
            params[key] = part(value, key)
            params[f"{key}_cache_secret_key"] = _image_cache_key(value)
    for key, prefix in (("reference_image_multiple", "ref_multiple_"), ("director_reference_images", "director_ref_")):
        values = params.pop(key, None)
        if values:
            params[f"{key}_cached"] = [
                {"cache_secret_key": _image_cache_key(v), "data": part(v, f"{prefix}{i}")} for i, v in enumerate(values)
            ]
    return [(name, base64.b64decode(b64)) for b64, name in names.items()]


class GenerateImageInfer(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    """Endpoint"""

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
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

    input: str = "1girl"
    model: ModelTypeAlias = Model.NAI_DIFFUSION_5_FULL
    action: str | Action = Field(Action.GENERATE, description="Mode for img generate")
    parameters: Params
    use_new_shared_trial: bool = False
    recaptcha_token: str | None = None
    """
    reCAPTCHA Enterprise token the web client attaches to free-trial generations.
    Not produced by this library; pass one through only if you already hold it.
    """
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

        # Add quality prompt based on qualityToggle / qualityPresetId
        modifier = get_quality_suffix(self.model, self.parameters.qualityPresetId)
        quality_tags, suffix = modifier.qualityTags, modifier.suffix
        quality_preset = self.parameters.qualityPresetId
        if isinstance(quality_preset, Enum):
            quality_preset = quality_preset.value
        use_quality = bool(self.parameters.qualityToggle and quality_preset != "none")
        if not use_quality:
            quality_tags, suffix = "", ""
        # Transparent BG (V5): the web client puts "transparent background" in front of the
        # quality suffix, or alone when quality tags are off (addQualityToPrompt, 2026-10 bundle).
        transparent = bool(self.parameters.tag_hint_transparent_background) and is_v5_model(self.model)
        if transparent:
            self.parameters.straight_alpha = True
            if "transparent background" not in self.input:
                suffix = ", transparent background" + suffix
            else:
                transparent = False  # already written by the user, only the quality tags are left to add

        def enhance_text_part(_part, _quality_tags, _suffix):
            text_parts = _part.split(" Text:")
            enhanced_text_parts = [
                _quality_tags + text_part + _suffix + ("." if _suffix and len(text_parts) > 1 else "")
                if index == 0
                else text_part
                for index, text_part in enumerate(text_parts)
            ]
            return " Text:".join(enhanced_text_parts)

        def enhance_simple_part(_part, _quality_tags, _suffix):
            match = re.search(r"(:[\d.]+$)", _part)
            matched_value = match.group(0) if match else None
            core_part = _part[: -len(matched_value)] if matched_value else _part
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
                    enhanced_parts = [enhance_simple_part(part, quality_tags, suffix) for part in parts]
                    return "|".join(enhanced_parts)
            except Exception as e:
                logger.error(
                    f"Failed to enhance `{_prompt}` because {e},"
                    f"Report this issue to https://github.com/LLMKIRA/novelai-python/issues"
                )
                return _prompt

        if use_quality or transparent:
            logger.debug("Adding quality / transparent-background tags to the input prompt.")
            self.input = enhance_message(self.input)

        if self._mutual_exclusion:
            logger.debug("Mutual exclusion is enabled, will modify negative prompt.")
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
    def _build_v5_params(self):
        """
        params_version 4 (NAI V5): the web client names presets instead of numbering them.
        :return: self
        """
        if is_v5_model(self.model) and self.parameters.params_version < 4:
            logger.warning(f"{self.model} requires params_version 4, upgrading request shape.")
            self.parameters.params_version = 4
        if self.parameters.params_version < 4:
            return self
        if self.model in V5_MEDIUM_MODEL_LIST:
            # fixedSettings in the web client
            self.parameters.steps = 14
            self.parameters.sampler = Sampler.K_EULER_ANCESTRAL
            self.parameters.ucPresetId = "heavy"
        if self.parameters.ucPresetId is None and self.parameters.ucPreset is not None:
            uc_preset = self.parameters.ucPreset
            if isinstance(uc_preset, Enum):
                uc_preset = uc_preset.value
            self.parameters.ucPresetId = get_uc_preset_id(self.model, uc_preset)
        if self.parameters.qualityPresetId is None:
            self.parameters.qualityPresetId = (
                QualityPreset.STANDARD if self.parameters.qualityToggle else QualityPreset.NONE
            )
        if self.parameters.tag_hint_transparent_background is not True:
            # the web client deletes the key unless Transparent BG is on (t8 constructor, 2026-10 bundle)
            self.parameters.tag_hint_transparent_background = None
        if is_v5_model(self.model) and self.parameters.image_format is None:
            self.parameters.image_format = ImageFormat.WEBP
        return self

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
                if get_supported_params(self.model).hasFurryMode and base_caption.startswith("fur dataset, "):
                    base_caption = base_caption.replace("fur dataset, ", "")
                self.parameters.v4_prompt = V4Prompt.build_from_character_prompts(
                    base_caption=base_caption, character_prompts=self.parameters.characterPrompts
                )
            if self.parameters.v4_negative_prompt is None:
                self.parameters.v4_negative_prompt = V4NegativePrompt.build_from_character_prompts(
                    negative_prompt=self.parameters.negative_prompt,
                    character_prompts=self.parameters.characterPrompts,
                    legacy_uc=self.parameters.legacy_uc,
                )
        if not get_supported_params(self.model).vibetransfer:
            if self.parameters.reference_image_multiple:
                logger.warning("Vibe transfer is not supported for this model.")
            self.parameters.reference_image_multiple = None  # Auto exclude None values
            self.parameters.reference_information_extracted_multiple = None  # Auto exclude None values
            self.parameters.reference_strength_multiple = None  # Auto exclude None values

        if get_supported_params(self.model).encodedVibes and any(
            isinstance(ref, str) and ref.startswith("iVBORw0KGgo")
            for ref in self.parameters.reference_image_multiple or []
        ):
            # the web client never sends raw images here for V4/V4.5: it calls /ai/encode-vibe first
            logger.warning(
                f"{self.model} takes encoded vibes: pass EncodeVibe(...).request(...).vibe_b64, not a PNG image."
            )

        if self.parameters.director_reference_images and not supports_character_reference(self.model):
            raise ValueError(f"Character reference needs a V4.5 model, {self.model} does not take it")

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
            limit = get_max_characters(self.model)
            if len(self.parameters.characterPrompts) > limit:
                raise ValueError(
                    f"{self.model} takes at most {limit} characters, got {len(self.parameters.characterPrompts)}"
                )
            self.parameters.use_coords = any([c.center != PositionMap.AUTO for c in self.parameters.characterPrompts])

            if get_supported_params(self.model).v4Prompts and self.parameters.v4_prompt is not None:
                self.parameters.v4_prompt.use_coords = self.parameters.use_coords
        # Mix Prompt Warning
        if self.input.count("|") > 6:
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
        if self.parameters.sampler in [Sampler.DDIM, Sampler.DDIM_V3]:
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
            Sampler.K_DPM_FAST,
        ]:
            self.parameters.noise_schedule = None

        if (
            self.parameters.sampler == Sampler.K_EULER_ANCESTRAL
            and self.parameters.noise_schedule != NoiseSchedule.NATIVE
        ):
            self.parameters.deliberate_euler_ancestral_bug = False
            self.parameters.prefer_brownian = True

        if self.parameters.skip_cfg_above_sigma is not None:
            scale_divisor, weight = (1, 3) if self.model == Model.DALLE_MINI else (8, 4)
            dimensions_scaled = [
                math.floor(self.parameters.width) / scale_divisor,
                math.floor(self.parameters.height) / scale_divisor,
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
        if self.action == Action.IMG2IMG and self.parameters.extra_noise_seed is None:
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

        if (
            get_supported_params(self.model).img2imgInpainting
            and self.parameters.mask
            and self.parameters.inpaintImg2ImgStrength != 1
        ):
            self.parameters.color_correct = True

        return self

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/generate-image"

    @property
    def stream_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/generate-image-stream"

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
            raise ValueError("Failed to calculate cost") from e

    @staticmethod
    def build_generate(
        prompt: str,
        *,
        model: Model | str = Model.NAI_DIFFUSION_5_FULL,
        negative_prompt: str | None = None,
        ucPreset: UCPresetTypeAlias = None,
        sm: bool | None = None,
        steps: int | None = None,
        seed: int | None = None,
        sampler: Sampler | str = None,
        width: int | None = None,
        height: int | None = None,
        add_original_image: bool | None = None,
        character_prompts: list[Character] | None = None,
        reference_image_multiple: list[str | bytes] | None = None,
        reference_strength_multiple: list[float] | None = None,
        reference_information_extracted_multiple: list[float] | None = None,
        qualityToggle: bool | None = None,
        decrisp_mode: bool | None = None,
        variety_boost: bool | None = None,
        furry_mode: bool | None = None,
        use_trial: bool = False,
        transparent_background: bool | None = None,
        character_references: list[CharacterReference] | None = None,
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
        :param transparent_background: V5 only: transparent background, as the web client's "Transparent BG".
        :param character_references: V4.5 only: Precise Reference images (character / style / costume...).
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
        if transparent_background is not None:
            params.tag_hint_transparent_background = transparent_background
        if character_references:
            for key, value in CharacterReference.to_params(character_references).items():
                setattr(params, key, value)
        return GenerateImageInfer(
            input=prompt, model=model, action=Action.GENERATE, parameters=params, use_new_shared_trial=use_trial
        )

    @staticmethod
    def build_img2img(
        prompt: str,
        *,
        model: Model | str = Model.NAI_DIFFUSION_4_5_FULL,
        image: bytes | str,
        strength: float | None = None,
        noise: float | None = None,
        seed: int | None = None,
        extra_noise_seed: int | None = None,
        negative_prompt: str | None = None,
        ucPreset: UCPresetTypeAlias = None,
        steps: int | None = None,
        sampler: Sampler | str = None,
        width: int | None = None,
        height: int | None = None,
        add_original_image: bool | None = None,
        character_prompts: list[Character] | None = None,
        reference_image_multiple: list[str | bytes] | None = None,
        reference_strength_multiple: list[float] | None = None,
        reference_information_extracted_multiple: list[float] | None = None,
        qualityToggle: bool | None = None,
        decrisp_mode: bool | None = None,
        variety_boost: bool | None = None,
        use_trial: bool = True,
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
            input=prompt, model=model, action=Action.IMG2IMG, parameters=params, use_new_shared_trial=use_trial
        )

    @staticmethod
    def build_infill(
        prompt: str,
        *,
        model: Model | str,
        image: bytes | str,
        mask: bytes | str,
        strength: float | None = None,
        negative_prompt: str | None = None,
        ucPreset: UCPresetTypeAlias = None,
        steps: int | None = None,
        seed: int | None = None,
        sampler: Sampler | str = None,
        width: int | None = None,
        height: int | None = None,
        add_original_image: bool | None = None,
        character_prompts: list[Character] | None = None,
        reference_image_multiple: list[str | bytes] | None = None,
        reference_strength_multiple: list[float] | None = None,
        reference_information_extracted_multiple: list[float] | None = None,
        qualityToggle: bool | None = None,
        decrisp_mode: bool | None = None,
        variety_boost: bool | None = None,
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

        return GenerateImageInfer(input=prompt, model=model, action=Action.INFILL, parameters=params)

    @staticmethod
    def _iter_msgpack_frames(buffer: bytearray):
        """Yield complete [uint32 BE length][msgpack] frames from ``buffer``, leaving partial data in place."""
        while len(buffer) >= 4:
            length = int.from_bytes(buffer[:4], "big")
            if len(buffer) < 4 + length:
                return
            frame = bytes(buffer[4 : 4 + length])
            del buffer[: 4 + length]
            yield msgpack.unpackb(frame, raw=False)

    async def request_stream(
        self,
        session: Union[AsyncSession, "CredentialBase"],
        *,
        override_headers: dict | None = None,
        limiter: DailyImageLimiter | bool | None = True,
    ) -> AsyncIterator[ImageStreamEvent]:
        """
        **Stream a generation**: intermediate previews and the final image per sample,
        the way the web client does for models with ``streamedResponses`` (V5 family).

        Yields ImageStreamEvent; ``event.is_final`` carries the finished sample bytes.

        :param session: Async session object or credential-based session.
        :param override_headers: Headers to override the default headers.
        :param limiter: see :meth:`request`.
        :raises DailyLimitExceeded: If the local image budget is used up (no request is sent).
        :raises APIError / AuthError / ConcurrentGenerationError / SessionHttpError: as :meth:`request`.
        """
        if limiter is True:
            limiter = get_default_limiter()
        elif limiter is False:
            limiter = None
        if limiter is not None:
            limiter.check(self.parameters.n_samples)

        request_data = self.model_dump(mode="json", exclude_none=True)
        if self.parameters.params_version >= 4:
            # the web client sends this key explicitly as null (live sample 2026-10-16)
            request_data["parameters"].setdefault("skip_cfg_above_sigma", None)
        request_data["parameters"]["stream"] = "msgpack"
        files = split_image_parts(request_data)
        body, content_type = build_multipart_request(json.dumps(request_data).encode("utf-8"), files)
        finals = 0
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            try:
                self.ensure_session_has_post_method(sess)
                response = await sess.post(
                    self.stream_url,
                    data=body,
                    headers={"Content-Type": content_type},
                    stream=True,
                )
                if response.status_code >= 400:
                    error_message = await self.handle_error_response(response, request_data)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400, 401, 402]:
                        raise AuthError(message, request=request_data, code=status_code, response=error_message)
                    if status_code == 429:
                        raise ConcurrentGenerationError(
                            message, request=request_data, code=status_code, response=error_message
                        )
                    raise APIError(message, request=request_data, code=status_code, response=error_message)

                buffer = bytearray()
                async for chunk in response.aiter_content():
                    buffer.extend(chunk)
                    for frame in self._iter_msgpack_frames(buffer):
                        event = ImageStreamEvent(
                            event_type=str(frame.get("event_type", "")),
                            samp_ix=int(frame.get("samp_ix", 0) or 0),
                            step_ix=frame.get("step_ix"),
                            image=frame.get("image"),
                            message=frame.get("message"),
                        )
                        if event.event_type == "error":
                            # NovelAI fails mid-stream with HTTP 200 and an error frame, e.g.
                            # {event_type: error, code: 500, message: "Error generating image..."}
                            code = frame.get("code") or 500
                            raise APIError(
                                event.message or "Error event in the image stream",
                                request=request_data,
                                code=code,
                                response=frame,
                            )
                        if event.is_final:
                            finals += 1
                        yield event
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.") from exc
        if limiter is not None and finals:
            limiter.consume(finals)

    @retry_on_server_error()
    async def request(
        self,
        session: Union[AsyncSession, "CredentialBase"],
        *,
        override_headers: dict | None = None,
        limiter: DailyImageLimiter | bool | None = True,
    ) -> ImageGenerateResp:
        """
        **Generate images using NovelAI's diffusion models.**

        According to our Terms of Service, all generation requests must be initiated by a human action. Automating text
        or image generation to create excessive load on our systems is not allowed.

        :param override_headers: Headers to override the default headers.
        :param session: Async session object or credential-based session.
        :param limiter: Local image budget. ``True`` uses the process-wide limiter
                        (``NOVELAI_DAILY_IMAGE_LIMIT``, default 2500 per 24h window),
                        a ``DailyImageLimiter`` instance uses that one, ``False``/``None`` skips the check.
        :return: ImageGenerateResp containing the response data and metadata.
        :raises DailyLimitExceeded: If the local image budget is used up (no request is sent).
        :raises AuthError: If the request is unauthorized.
        :raises APIError: If the API returns an error.
        :raises ConcurrentGenerationError: If the request is rate-limited.
        :raises SessionHttpError: If an HTTP error occurs.
        :raises DataSerializationError: If an error occurs while processing the response data.
        """
        if limiter is True:
            limiter = get_default_limiter()
        elif limiter is False:
            limiter = None
        if limiter is not None:
            limiter.check(self.parameters.n_samples)

        # Prepare request data
        request_data = self.model_dump(mode="json", exclude_none=True)
        if self.parameters.params_version >= 4:
            # the web client sends this key explicitly as null (live sample 2026-10-16)
            request_data["parameters"].setdefault("skip_cfg_above_sigma", None)
        files = split_image_parts(request_data) if self.parameters.params_version >= 4 else []
        request_json = json.dumps(request_data).encode("utf-8")
        if self.parameters.params_version >= 4:
            # the web client wraps every generate-image call in multipart/form-data
            body, content_type = build_multipart_request(request_json, files)
        else:
            body, content_type = request_json, "application/json"
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)

            # Log the request data (sanitize sensitive content)
            try:
                log_data = deepcopy(request_data)
                if self.parameters.image:
                    log_data["parameters"]["image"] = "base64 data hidden"
                if self.parameters.mask:
                    log_data["parameters"]["mask"] = "base64 data hidden"
                if self.parameters.reference_image_multiple:
                    log_data["parameters"]["reference_image_multiple"] = ["base64 data hidden"] * len(
                        self.parameters.reference_image_multiple
                    )
                logger.debug(f"Request Data: {json.dumps(log_data, indent=2)}")
            except Exception as e:
                logger.warning(f"Failed to log request data: {e}")

            # Perform request and handle response
            try:
                self.ensure_session_has_post_method(sess)
                response = await sess.post(
                    self.base_url,
                    data=body,
                    headers={"Content-Type": content_type},
                )
                # Validate response content type and status code
                response_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                if response_type not in ZIP_CONTENT_TYPES + IMAGE_CONTENT_TYPES or response.status_code >= 400:
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

                # Unpack the ZIP response (or accept a bare image, which V5 may return for webp)
                try:
                    unzip_content = []
                    bare_ext = _sniff_image_extension(response.content)
                    if bare_ext:
                        unzip_content.append((f"image_0.{bare_ext}", response.content))
                    else:
                        zip_file = ZipFile(BytesIO(response.content))
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
                    if limiter is not None:
                        limiter.consume(max(len(unzip_content), 1))
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
                raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.") from exc
            except APIError as e:
                raise e
            except Exception as e:
                logger.exception("Unexpected error occurred during the request.")
                raise Exception("An unexpected error occurred.") from e
