# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:10
# @Author  : sudoskys
# @File    : _enum.py
# @Software: PyCharm
from enum import Enum, IntEnum
from typing import List, Optional, Union

from pydantic.dataclasses import dataclass


class Sampler(Enum):
    PLMS = "plms"
    DDIM = "ddim"
    K_EULER = "k_euler"
    K_EULER_ANCESTRAL = "k_euler_ancestral"
    K_DPM_2 = "k_dpm_2"
    K_DPM_2_ANCESTRAL = "k_dpm_2_ancestral"
    K_LMS = "k_lms"
    K_DPMPP_2S_ANCESTRAL = "k_dpmpp_2s_ancestral"
    K_DPMPP_SDE = "k_dpmpp_sde"
    K_DPMPP_2M = "k_dpmpp_2m"
    K_DPM_ADAPTIVE = "k_dpm_adaptive"
    K_DPM_FAST = "k_dpm_fast"
    K_DPMPP_2M_SDE = "k_dpmpp_2m_sde"
    K_DPMPP_3M_SDE = "k_dpmpp_3m_sde"
    DDIM_V3 = "ddim_v3"
    NAI_SMEA = "nai_smea"
    NAI_SMEA_DYN = "nai_smea_dyn"


class NoiseSchedule(Enum):
    NATIVE = "native"
    KARRAS = "karras"
    EXPONENTIAL = "exponential"
    POLYEXPONENTIAL = "polyexponential"


class UCPreset(IntEnum):
    TYPE0 = 0
    TYPE1 = 1
    TYPE2 = 2
    TYPE3 = 3


class Action(Enum):
    GENERATE = "generate"
    """Generate Image"""
    IMG2IMG = "img2img"
    """Image to Image"""
    INFILL = "infill"
    """Inpainting"""


class ControlNetModel(Enum):
    HED = "hed"
    """边缘检测"""
    MIDAS = "midas"
    """景深"""
    FAKE_SCRIBBLE = "fake_scribble"
    """伪涂鸦"""
    UNIFORMER = "uniformer"
    """风景生成"""

    # Unusable
    CANNY = "canny"
    """边缘检测方法之一"""
    DEPTH = "depth"
    """深度信息提取"""
    MLSD = "mlsd"
    """(建筑)线条检测"""
    NORMAL = "normal"
    """法线信息提取"""
    SCRIBBLE = "scribble"
    """手绘涂鸦风格生成"""
    SEG = "seg"
    """分割算法"""


class Resolution(Enum):
    RES_512_768 = (512, 768)
    RES_768_512 = (768, 512)
    RES_640_640 = (640, 640)
    RES_832_1216 = (832, 1216)
    RES_1216_832 = (1216, 832)
    RES_1024_1024 = (1024, 1024)
    RES_1024_1536 = (1024, 1536)
    RES_1536_1024 = (1536, 1024)
    RES_1472_1472 = (1472, 1472)
    RES_1088_1920 = (1088, 1920)
    RES_1920_1088 = (1920, 1088)


class Model(Enum):
    NAI_DIFFUSION_3 = "nai-diffusion-3"
    NAI_DIFFUSION_3_INPAINTING = "nai-diffusion-3-inpainting"
    NAI_DIFFUSION_FURRY_3 = "nai-diffusion-furry-3"
    NAI_DIFFUSION_FURRY_3_INPAINTING = "nai-diffusion-furry-3-inpainting"
    NAI_DIFFUSION = "nai-diffusion"
    NAI_DIFFUSION_2 = "nai-diffusion-2"
    NAI_DIFFUSION_INPAINTING = "nai-diffusion-inpainting"

    SAFE_DIFFUSION = "safe-diffusion"
    SAFE_DIFFUSION_INPAINTING = "safe-diffusion-inpainting"

    NAI_DIFFUSION_FURRY = "nai-diffusion-furry"

    FURRY_DIFFUSION_INPAINTING = "furry-diffusion-inpainting"

    CUSTOM = "custom"
    STABLE_DIFFUSION = "stable-diffusion"
    WAIFU_DIFFUSION = "waifu-diffusion"
    CURATED_DIFFUSION_TEST = "curated-diffusion-test"
    NAI_DIFFUSION_XL = "nai-diffusion-xl"


class ModelGroups(Enum):
    STABLE_DIFFUSION = "stable_diffusion"
    STABLE_DIFFUSION_GROUP_2 = "stable_diffusion_group2"
    STABLE_DIFFUSION_XL = "stable_diffusion_xl"
    STABLE_DIFFUSION_XL_FURRY = "stable_diffusion_xl_furry"


INPAINTING_MODEL_LIST = [
    Model.NAI_DIFFUSION_3_INPAINTING,
    Model.NAI_DIFFUSION_INPAINTING,
    Model.SAFE_DIFFUSION_INPAINTING,
    Model.FURRY_DIFFUSION_INPAINTING,
    Model.NAI_DIFFUSION_FURRY_3_INPAINTING
]

PROMOTION = {
    "Stable Diffusion 1D44365E": Model.SAFE_DIFFUSION,
    "Stable Diffusion F4D50568": Model.SAFE_DIFFUSION,
    "Stable Diffusion 81274D13": Model.NAI_DIFFUSION,
    "Stable Diffusion 3B3287AF": Model.NAI_DIFFUSION,
    "Stable Diffusion 4CC42576": Model.NAI_DIFFUSION_FURRY,
    "Stable Diffusion 1D09C008": Model.NAI_DIFFUSION_FURRY,
    "Stable Diffusion 1D09D794": Model.NAI_DIFFUSION_FURRY,
    "Stable Diffusion F64BA557": Model.NAI_DIFFUSION_FURRY,
    "Stable Diffusion 49BFAF6A": Model.NAI_DIFFUSION_2,
    "Stable Diffusion F1022D28": Model.NAI_DIFFUSION_2,
    "Stable Diffusion XL B0BDF6C1": Model.NAI_DIFFUSION_3,
    "Stable Diffusion XL C1E1DE52": Model.NAI_DIFFUSION_3,
    "Stable Diffusion XL 7BCCAA2C": Model.NAI_DIFFUSION_3,
    "Stable Diffusion XL 8BA2AF87": Model.NAI_DIFFUSION_3,
    "Stable Diffusion XL 4BE8C60C": Model.NAI_DIFFUSION_FURRY_3,
    "Stable Diffusion XL C8704949": Model.NAI_DIFFUSION_FURRY_3,
    "Stable Diffusion XL 37C2B166": Model.NAI_DIFFUSION_FURRY_3,
    "Stable Diffusion XL 9CC2F394": Model.NAI_DIFFUSION_FURRY_3,
}

ModelTypeAlias = Optional[Union[Model, str]]
ImageBytesTypeAlias = Optional[Union[str, bytes]]
UCPresetTypeAlias = Optional[Union[UCPreset, int]]


def get_supported_noise_schedule(sample_type: Sampler) -> List[NoiseSchedule]:
    """
    Get supported noise schedule for a given sample type
    :param sample_type: Sampler
    :return: List[NoiseSchedule]
    """
    if sample_type in [
        Sampler.K_EULER_ANCESTRAL,
        Sampler.K_DPMPP_2S_ANCESTRAL,
        Sampler.K_DPMPP_2M,
        Sampler.K_DPMPP_2M_SDE,
        Sampler.K_DPMPP_SDE,
        Sampler.K_EULER
    ]:
        return [
            NoiseSchedule.NATIVE,
            NoiseSchedule.KARRAS,
            NoiseSchedule.EXPONENTIAL,
            NoiseSchedule.POLYEXPONENTIAL
        ]
    elif sample_type in [Sampler.K_DPM_2]:
        return [
            NoiseSchedule.EXPONENTIAL,
            NoiseSchedule.POLYEXPONENTIAL
        ]
    else:
        return []


def get_default_noise_schedule(sample_type: Sampler) -> NoiseSchedule:
    """
    Get default noise schedule for a given sample type
    :param sample_type: Sampler
    :return: NoiseSchedule
    """
    if sample_type in [
        Sampler.K_EULER_ANCESTRAL,
        Sampler.K_DPMPP_2S_ANCESTRAL,
        Sampler.K_DPMPP_2M,
        Sampler.K_DPMPP_2M_SDE,
        Sampler.K_DPMPP_SDE,
        Sampler.K_EULER
    ]:
        return NoiseSchedule.KARRAS
    elif sample_type in [Sampler.K_DPM_2]:
        return NoiseSchedule.EXPONENTIAL
    else:
        return NoiseSchedule.NATIVE


def get_model_group(model: ModelTypeAlias) -> ModelGroups:
    if isinstance(model, Enum):
        model = model.value
    else:
        model = str(model)
    mapping = {
        "stable-diffusion": ModelGroups.STABLE_DIFFUSION,
        "nai-diffusion": ModelGroups.STABLE_DIFFUSION,
        "safe-diffusion": ModelGroups.STABLE_DIFFUSION,
        "waifu-diffusion": ModelGroups.STABLE_DIFFUSION,
        "nai-diffusion-furry": ModelGroups.STABLE_DIFFUSION,
        "curated-diffusion-test": ModelGroups.STABLE_DIFFUSION,
        "nai-diffusion-inpainting": ModelGroups.STABLE_DIFFUSION,
        "safe-diffusion-inpainting": ModelGroups.STABLE_DIFFUSION,
        "furry-diffusion-inpainting": ModelGroups.STABLE_DIFFUSION,
        "nai-diffusion-2": ModelGroups.STABLE_DIFFUSION_GROUP_2,
        "nai-diffusion-xl": ModelGroups.STABLE_DIFFUSION_XL,
        "nai-diffusion-3": ModelGroups.STABLE_DIFFUSION_XL,
        "nai-diffusion-3-inpainting": ModelGroups.STABLE_DIFFUSION_XL,
        "custom": ModelGroups.STABLE_DIFFUSION_XL,
        "nai-diffusion-furry-3": ModelGroups.STABLE_DIFFUSION_XL_FURRY,
        "nai-diffusion-furry-3-inpainting": ModelGroups.STABLE_DIFFUSION_XL_FURRY,
    }
    return mapping.get(model, ModelGroups.STABLE_DIFFUSION)


def get_default_uc_preset(model: ModelTypeAlias, uc_preset: int) -> str:
    if isinstance(model, Enum):
        model = model.value
    if isinstance(uc_preset, Enum):
        uc_preset = uc_preset.value

    @dataclass
    class UcPrompt:
        label: str
        text: str

    mapper = {
        ModelGroups.STABLE_DIFFUSION: [
            UcPrompt("lowQualityPlusBadAnatomy",
                     text="lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"),
            UcPrompt("lowQuality",
                     text="lowres, text, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"),
            UcPrompt("none", text="lowres")
        ],
        ModelGroups.STABLE_DIFFUSION_GROUP_2: [
            UcPrompt("heavy",
                     text="lowres, bad, text, error, missing, extra, fewer, cropped, jpeg artifacts, worst quality, bad quality, watermark, displeasing, unfinished, chromatic aberration, scan, scan artifacts"),
            UcPrompt("light", text="lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing"),
            UcPrompt("none", text="lowres")
        ],
        ModelGroups.STABLE_DIFFUSION_XL: [
            UcPrompt("heavy",
                     text="lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract]"),
            UcPrompt("light", text="lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing"),
            UcPrompt("humanFocus",
                     text="lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, glowing eyes"),
            UcPrompt("none", text="lowres")
        ],
        ModelGroups.STABLE_DIFFUSION_XL_FURRY: [
            UcPrompt("heavy",
                     text="{{worst quality}}, [displeasing], {unusual pupils}, guide lines, {{unfinished}}, {bad}, url, artist name, {{tall image}}, mosaic, {sketch page}, comic panel, impact (font), [dated], {logo}, ych, {what}, {where is your god now}, {distorted text}, repeated text, {floating head}, {1994}, {widescreen}, absolutely everyone, sequence, {compression artifacts}, hard translated, {cropped}, {commissioner name}, unknown text, high contrast"),
            UcPrompt("light",
                     text="{worst quality}, guide lines, unfinished, bad, url, tall image, widescreen, compression artifacts, unknown text"),
            UcPrompt("none", text="lowres")
        ],
    }
    model_group = get_model_group(model)
    prompts: List[UcPrompt] = mapper.get(model_group, [UcPrompt("none", "lowres")])
    if 0 <= uc_preset < len(prompts):
        return prompts[uc_preset].text
    else:
        return "lowres"
