import base64
import random
from io import BytesIO
from typing import Optional, List, Union, Tuple

import cv2
import numpy as np
from PIL import Image
from loguru import logger
from pydantic import BaseModel, Field, model_validator, field_validator

from novelai_python.sdk.ai._enum import Sampler, UCPresetTypeAlias, NoiseSchedule, ImageBytesTypeAlias, ControlNetModel, \
    Model
from novelai_python.sdk.ai.generate_image.schema import Character, V4Prompt, V4NegativePrompt


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
        default_factory=list,
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

    color_correct: Optional[bool] = None
    """For Inpaint"""
    inpaintImg2ImgStrength: Optional[float] = Field(None, ge=0, le=1, multiple_of=0.01)
    """For SameFeel"""

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

    autoSmea: Optional[bool] = False
    normalize_reference_strength_multiple: bool = True
    legacy_uc: bool = False

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


def get_default_params(model: Model = None) -> Params:
    """
    Get default parameters for a given model

    :param model: Model to get default parameters for
    :return: Params instance with default values
    """
    if model in [
        Model.STABLE_DIFFUSION,
        Model.NAI_DIFFUSION,
        Model.SAFE_DIFFUSION,
        Model.WAIFU_DIFFUSION,
        Model.NAI_DIFFUSION_FURRY,
        Model.CURATED_DIFFUSION_TEST,
    ]:
        return Params(
            width=512,
            height=768,
            scale=10.0,
            sampler=Sampler.K_EULER_ANCESTRAL,
            steps=28,
            n_samples=1,
            strength=0.7,
            noise=0.0,
            ucPreset=0,
            qualityToggle=True,
            autoSmea=False,
            sm=False,
            sm_dyn=False,
            dynamic_thresholding=False,
            controlnet_strength=1.0,
            legacy=False,
            add_original_image=True,
            cfg_rescale=0.0,
            noise_schedule=NoiseSchedule.NATIVE,
            legacy_v3_extend=False,
            skip_cfg_above_sigma=None,
            params_version=3
        )

    if model == Model.NAI_DIFFUSION_2:
        return Params(
            width=832,
            height=1216,
            scale=10.0,
            sampler=Sampler.K_EULER_ANCESTRAL,
            steps=28,
            n_samples=1,
            strength=0.7,
            noise=0.0,
            ucPreset=0,
            qualityToggle=True,
            autoSmea=True,
            sm=False,
            sm_dyn=False,
            dynamic_thresholding=False,
            controlnet_strength=1.0,
            legacy=False,
            add_original_image=True,
            cfg_rescale=0.0,
            noise_schedule=NoiseSchedule.NATIVE,
            legacy_v3_extend=False,
            skip_cfg_above_sigma=None,
            params_version=3
        )

    if model in [
        Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
        Model.NAI_DIFFUSION_4_FULL,
        Model.NAI_DIFFUSION_4_FULL_INPAINTING,
        Model.NAI_DIFFUSION_4_CURATED_INPAINTING,
    ]:
        return Params(
            width=832,
            height=1216,
            scale=5.5,
            sampler=Sampler.K_EULER_ANCESTRAL,
            steps=23,
            n_samples=1,
            strength=0.7,
            noise=0.0,
            ucPreset=0,
            qualityToggle=True,
            autoSmea=False,
            sm=False,
            sm_dyn=False,
            dynamic_thresholding=False,
            controlnet_strength=1.0,
            legacy=False,
            add_original_image=True,
            cfg_rescale=0.0,
            noise_schedule=NoiseSchedule.KARRAS,
            legacy_v3_extend=False,
            skip_cfg_above_sigma=None,
            use_coords=False,
            legacy_uc=False,
            normalize_reference_strength_multiple=True,
            inpaintImg2ImgStrength=1.0,
            params_version=3
        )

    if model in [
        Model.CUSTOM,
        Model.NAI_DIFFUSION_4_5_CURATED,
        Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING,
        Model.NAI_DIFFUSION_4_5_FULL,
        Model.NAI_DIFFUSION_4_5_FULL_INPAINTING,
    ]:
        return Params(
            width=832,
            height=1216,
            scale=5.0,
            sampler=Sampler.K_EULER_ANCESTRAL,
            steps=23,
            n_samples=1,
            strength=0.7,
            noise=0.0,
            ucPreset=0,
            qualityToggle=True,
            autoSmea=False,
            sm=False,
            sm_dyn=False,
            dynamic_thresholding=False,
            controlnet_strength=1.0,
            legacy=False,
            add_original_image=True,
            cfg_rescale=0.0,
            noise_schedule=NoiseSchedule.KARRAS,
            legacy_v3_extend=False,
            skip_cfg_above_sigma=None,
            use_coords=False,
            legacy_uc=False,
            normalize_reference_strength_multiple=True,
            inpaintImg2ImgStrength=1.0,
            params_version=3
        )

    if model == Model.NAI_DIFFUSION_3:
        return Params(
            width=832,
            height=1216,
            scale=5.0,
            sampler=Sampler.K_EULER_ANCESTRAL,
            steps=23,
            n_samples=1,
            strength=0.7,
            noise=0.0,
            ucPreset=0,
            qualityToggle=True,
            autoSmea=True,
            sm=False,
            sm_dyn=False,
            dynamic_thresholding=False,
            controlnet_strength=1.0,
            legacy=False,
            add_original_image=True,
            cfg_rescale=0.0,
            noise_schedule=NoiseSchedule.KARRAS,
            legacy_v3_extend=False,
            skip_cfg_above_sigma=None,
            params_version=3
        )

    if model == Model.NAI_DIFFUSION_FURRY_3:
        return Params(
            width=832,
            height=1216,
            scale=6.2,
            sampler=Sampler.K_EULER_ANCESTRAL,
            steps=23,
            n_samples=1,
            strength=0.7,
            noise=0.0,
            ucPreset=0,
            qualityToggle=True,
            autoSmea=True,
            sm=False,
            sm_dyn=False,
            dynamic_thresholding=False,
            controlnet_strength=1.0,
            legacy=False,
            add_original_image=True,
            cfg_rescale=0.0,
            noise_schedule=NoiseSchedule.KARRAS,
            legacy_v3_extend=False,
            skip_cfg_above_sigma=None,
            params_version=3
        )

    # Default parameters if model is not specified or not matched
    return Params(
        width=832,
        height=1216,
        scale=5.0,
        sampler=Sampler.K_EULER_ANCESTRAL,
        steps=23,
        n_samples=1,
        strength=0.7,
        noise=0.0,
        ucPreset=0,
        qualityToggle=True,
        autoSmea=False,
        sm=False,
        sm_dyn=False,
        dynamic_thresholding=False,
        controlnet_strength=1.0,
        legacy=False,
        add_original_image=True,
        cfg_rescale=0.0,
        noise_schedule=NoiseSchedule.NATIVE,
        legacy_v3_extend=False,
        skip_cfg_above_sigma=None,
        params_version=3
    )
