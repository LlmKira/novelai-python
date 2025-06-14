# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:10
# @Author  : sudoskys
# @File    : _enum.py
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
    """
    Nai Diffusion series
    """
    NAI_DIFFUSION_4_5_FULL = "nai-diffusion-4-5-full"
    NAI_DIFFUSION_4_5_FULL_INPAINTING = 'nai-diffusion-4-5-full-inpainting'

    NAI_DIFFUSION_4_5_CURATED = 'nai-diffusion-4-5-curated'
    NAI_DIFFUSION_4_5_CURATED_INPAINTING = 'nai-diffusion-4-5-curated-inpainting'

    NAI_DIFFUSION_4_CURATED_PREVIEW = "nai-diffusion-4-curated-preview"
    NAI_DIFFUSION_4_FULL = "nai-diffusion-4-full"
    NAI_DIFFUSION_4_FULL_INPAINTING = "nai-diffusion-4-full-inpainting"
    NAI_DIFFUSION_4_CURATED_INPAINTING = "nai-diffusion-4-curated-inpainting"

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
    DALLE_MINI = "dalle-mini"


class ModelGroups(Enum):
    STABLE_DIFFUSION = "stable_diffusion"
    STABLE_DIFFUSION_GROUP_2 = "stable_diffusion_group2"
    STABLE_DIFFUSION_XL = "stable_diffusion_xl"
    STABLE_DIFFUSION_XL_FURRY = "stable_diffusion_xl_furry"
    V4 = "v4"


INPAINTING_MODEL_LIST = [
    Model.NAI_DIFFUSION_3_INPAINTING,
    Model.NAI_DIFFUSION_INPAINTING,
    Model.SAFE_DIFFUSION_INPAINTING,
    Model.FURRY_DIFFUSION_INPAINTING,
    Model.NAI_DIFFUSION_FURRY_3_INPAINTING,
    Model.NAI_DIFFUSION_4_CURATED_INPAINTING,
    Model.NAI_DIFFUSION_4_FULL_INPAINTING,
    Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING,
    Model.NAI_DIFFUSION_4_5_FULL_INPAINTING,
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
    "Stable Diffusion XL 1120E6A9": Model.NAI_DIFFUSION_3,
    "Stable Diffusion XL 8BA2AF87": Model.NAI_DIFFUSION_3,
    "Stable Diffusion XL 4BE8C60C": Model.NAI_DIFFUSION_FURRY_3,
    "Stable Diffusion XL C8704949": Model.NAI_DIFFUSION_FURRY_3,
    "Stable Diffusion XL 37C2B166": Model.NAI_DIFFUSION_FURRY_3,
    "Stable Diffusion XL F306816B": Model.NAI_DIFFUSION_FURRY_3,
    "Stable Diffusion XL 9CC2F394": Model.NAI_DIFFUSION_FURRY_3,
    'NovelAI Diffusion V4.5 B9F340FD': Model.NAI_DIFFUSION_4_5_FULL,
    'NovelAI Diffusion V4.5 F3D95188': Model.NAI_DIFFUSION_4_5_FULL,
    'NovelAI Diffusion V4.5 5AB81C7C': Model.NAI_DIFFUSION_4_5_CURATED,
    "NovelAI Diffusion V4.5 B5A2A797": Model.NAI_DIFFUSION_4_5_CURATED,
    "NovelAI Diffusion V4 5AB81C7C": Model.NAI_DIFFUSION_4_5_CURATED,
    "NovelAI Diffusion V4 B5A2A797": Model.NAI_DIFFUSION_4_5_CURATED,
    "NovelAI Diffusion V4 37442FCA": Model.NAI_DIFFUSION_4_FULL,
    "NovelAI Diffusion V4 4F49EC75": Model.NAI_DIFFUSION_4_FULL,
    "NovelAI Diffusion V4 CA4B7203": Model.NAI_DIFFUSION_4_FULL,
    "NovelAI Diffusion V4 79F47848": Model.NAI_DIFFUSION_4_FULL,
    "NovelAI Diffusion V4 F6302A9D": Model.NAI_DIFFUSION_4_FULL,
    "NovelAI Diffusion V4 7ABFFA2A": Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
    "NovelAI Diffusion V4 C1CCBA86": Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
    "NovelAI Diffusion V4 770A9E12": Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
}

ModelTypeAlias = Optional[Union[Model, str]]
ImageBytesTypeAlias = Optional[Union[str, bytes]]
UCPresetTypeAlias = Optional[Union[UCPreset, int]]


@dataclass
class SupportCondition:
    controlnet: bool
    vibetransfer: bool
    scaleMax: int
    negativePromptGuidance: bool
    noiseSchedule: bool
    inpainting: bool
    cfgDelay: bool
    characterPrompts: bool
    v4Prompts: bool
    smea: bool
    smeaDyn: bool
    text: bool
    dynamicThresholding: bool
    autoSmea: bool
    v4_0legacyUC: bool
    scaleRecommendedMin: int
    scaleRecommendedMax: Optional[int]
    numericEmphasis: bool
    encodedVibes: bool
    cfgDelaySigma: int
    enhancePromptAdd: bool  # For enhance mode, see https://github.com/llmkira/novelai-python/blob/main/playground/enhance.py
    hasFurryMode: bool
    img2imgInpainting: bool


def get_supported_params(model: ModelTypeAlias):
    """
    Get supported parameters for a given model
    :param model: Model
    :return: SupportCondition
    """
    if isinstance(model, str):
        try:
            model = Model(model)
        except ValueError:
            pass
    if model in [
        Model.STABLE_DIFFUSION,
        Model.NAI_DIFFUSION,
        Model.SAFE_DIFFUSION,
        Model.WAIFU_DIFFUSION,
        Model.NAI_DIFFUSION_FURRY,
        Model.CURATED_DIFFUSION_TEST,
        Model.NAI_DIFFUSION_INPAINTING,
        Model.SAFE_DIFFUSION_INPAINTING,
        Model.FURRY_DIFFUSION_INPAINTING
    ]:
        return SupportCondition(
            controlnet=True,
            vibetransfer=False,
            scaleMax=25,
            negativePromptGuidance=False,
            noiseSchedule=False,
            inpainting=True,
            cfgDelay=False,
            characterPrompts=False,
            v4Prompts=False,
            smea=True,
            smeaDyn=False,
            text=False,
            dynamicThresholding=True,
            autoSmea=True,
            v4_0legacyUC=False,
            scaleRecommendedMin=6,
            scaleRecommendedMax=25,
            numericEmphasis=False,
            encodedVibes=False,
            cfgDelaySigma=19,
            enhancePromptAdd=False,
            hasFurryMode=False,
            img2imgInpainting=False
        )
    if model in [Model.NAI_DIFFUSION_2]:
        return SupportCondition(
            controlnet=True,
            vibetransfer=False,
            scaleMax=25,
            negativePromptGuidance=True,
            noiseSchedule=False,
            inpainting=True,
            cfgDelay=False,
            characterPrompts=False,
            v4Prompts=False,
            smea=True,
            smeaDyn=False,
            text=False,
            dynamicThresholding=True,
            autoSmea=True,
            v4_0legacyUC=False,
            scaleRecommendedMin=6,
            scaleRecommendedMax=25,
            numericEmphasis=False,
            encodedVibes=False,
            cfgDelaySigma=19,
            enhancePromptAdd=False,
            hasFurryMode=False,
            img2imgInpainting=False
        )
    if model in [
        Model.NAI_DIFFUSION_XL,
        Model.NAI_DIFFUSION_3,
        Model.NAI_DIFFUSION_3_INPAINTING,
        Model.NAI_DIFFUSION_FURRY_3,
        Model.NAI_DIFFUSION_FURRY_3_INPAINTING
    ]:
        return SupportCondition(
            controlnet=False,
            vibetransfer=True,
            scaleMax=10,
            negativePromptGuidance=True,
            noiseSchedule=True,
            inpainting=True,
            cfgDelay=True,
            characterPrompts=False,
            v4Prompts=False,
            smea=True,
            smeaDyn=True,
            text=False,
            dynamicThresholding=True,
            autoSmea=True,
            v4_0legacyUC=False,
            scaleRecommendedMin=2,
            scaleRecommendedMax=8,
            numericEmphasis=False,
            encodedVibes=False,
            cfgDelaySigma=19,
            enhancePromptAdd=False,
            hasFurryMode=False,
            img2imgInpainting=False
        )
    if model in [
        Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
        Model.NAI_DIFFUSION_4_CURATED_INPAINTING,
        Model.NAI_DIFFUSION_4_FULL,
        Model.NAI_DIFFUSION_4_FULL_INPAINTING,
    ]:
        return SupportCondition(
            controlnet=False,
            vibetransfer=True,
            scaleMax=10,
            negativePromptGuidance=True,
            noiseSchedule=True,
            inpainting=True,
            cfgDelay=True,
            characterPrompts=True,
            v4Prompts=True,
            smea=False,
            smeaDyn=False,
            text=True,
            dynamicThresholding=False,
            autoSmea=False,
            v4_0legacyUC=True,
            scaleRecommendedMin=2,
            scaleRecommendedMax=6,
            numericEmphasis=True,
            encodedVibes=True,
            cfgDelaySigma=19,
            enhancePromptAdd=False,
            hasFurryMode=True,
            img2imgInpainting=False
        )
    if model in [Model.CUSTOM]:
        return SupportCondition(
            controlnet=False,
            vibetransfer=True,
            scaleMax=10,
            negativePromptGuidance=True,
            noiseSchedule=True,
            inpainting=True,
            cfgDelay=True,
            characterPrompts=True,
            v4Prompts=True,
            smea=False,
            smeaDyn=False,
            text=True,
            dynamicThresholding=False,
            autoSmea=False,
            v4_0legacyUC=True,
            scaleRecommendedMin=0,
            scaleRecommendedMax=None,
            numericEmphasis=True,
            encodedVibes=True,
            cfgDelaySigma=58,
            enhancePromptAdd=False,
            hasFurryMode=True,
            img2imgInpainting=False
        )
    if model in [
        Model.NAI_DIFFUSION_4_5_CURATED,
        Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING,
        Model.NAI_DIFFUSION_4_5_FULL,
        Model.NAI_DIFFUSION_4_5_FULL_INPAINTING,
    ]:
        return SupportCondition(
            controlnet=False,
            vibetransfer=False,
            scaleMax=10,
            negativePromptGuidance=True,
            noiseSchedule=True,
            inpainting=True,
            cfgDelay=True,
            characterPrompts=True,
            v4Prompts=True,
            smea=False,
            smeaDyn=False,
            text=True,
            dynamicThresholding=False,
            autoSmea=False,
            v4_0legacyUC=False,
            scaleRecommendedMin=0,
            scaleRecommendedMax=None,
            numericEmphasis=True,
            encodedVibes=False,
            cfgDelaySigma=58,
            enhancePromptAdd=True,
            hasFurryMode=True,
            img2imgInpainting=False
        )
    return SupportCondition(
        controlnet=False,
        vibetransfer=False,
        scaleMax=25,
        negativePromptGuidance=False,
        noiseSchedule=False,
        inpainting=False,
        cfgDelay=False,
        characterPrompts=False,
        v4Prompts=False,
        smea=False,
        smeaDyn=False,
        text=False,
        dynamicThresholding=False,
        autoSmea=False,
        v4_0legacyUC=False,
        scaleRecommendedMin=0,
        scaleRecommendedMax=99,
        numericEmphasis=False,
        encodedVibes=False,
        cfgDelaySigma=19,
        enhancePromptAdd=False,
        hasFurryMode=False,
        img2imgInpainting=False
    )


@dataclass
class Modifier(object):
    qualityTags: str
    suffix: str


def find_model_by_hashcode(hashcode: str) -> ModelTypeAlias:
    if "NovelAI Diffusion V4.5" in hashcode:
        return PROMOTION.get(hashcode, Model.NAI_DIFFUSION_4_5_FULL)
    if "NovelAI Diffusion V4" in hashcode:
        return PROMOTION.get(hashcode, Model.NAI_DIFFUSION_4_CURATED_PREVIEW)
    return PROMOTION.get(hashcode, None)


def get_modifiers(model: Model) -> Modifier:
    """
    Get modifiers from model
    :param model:
    :return:
    """
    if model in [
        Model.CUSTOM,
        Model.NAI_DIFFUSION_4_5_FULL,
        Model.NAI_DIFFUSION_4_5_FULL_INPAINTING
    ]:
        return Modifier(
            qualityTags="",
            suffix=", very aesthetic, masterpiece, no text"
        )
    if model in [
        Model.NAI_DIFFUSION_4_5_CURATED,
        Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING
    ]:
        return Modifier(
            qualityTags="",
            suffix=", very aesthetic, location, masterpiece, no text, -0.8::feet::, rating:general"
        )
    if model in [
        Model.NAI_DIFFUSION_4_FULL,
        Model.NAI_DIFFUSION_4_FULL_INPAINTING,
    ]:
        return Modifier(
            qualityTags="",
            suffix=", no text, best quality, very aesthetic, absurdres"
        )
    if model in [
        Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
        Model.NAI_DIFFUSION_4_CURATED_INPAINTING,
    ]:
        return Modifier(
            qualityTags="",
            suffix=", rating:general, best quality, very aesthetic, absurdres"
        )
    if model in [Model.NAI_DIFFUSION_2]:
        return Modifier(
            qualityTags="very aesthetic, best quality, absurdres, ",
            suffix=""
        )
    if model in [
        Model.NAI_DIFFUSION_3,
        Model.NAI_DIFFUSION_3_INPAINTING
    ]:
        return Modifier(
            qualityTags="",
            suffix=", best quality, amazing quality, very aesthetic, absurdres"
        )
    if model in [
        Model.NAI_DIFFUSION_FURRY_3,
        Model.NAI_DIFFUSION_FURRY_3_INPAINTING
    ]:
        return Modifier(
            qualityTags="",
            suffix=", {best quality}, {amazing quality}"
        )
    return Modifier(
        qualityTags="masterpiece, best quality, ",
        suffix=""
    )


def get_supported_noise_schedule(sample_type: Sampler, model: Model) -> List[NoiseSchedule]:
    """
    Get supported noise schedule for a given sample type and model
    :param sample_type: Sampler
    :param model: Model
    :return: List[NoiseSchedule]
    """
    noise_schedule = get_sampler_supported_noise_schedule(sample_type)
    schedules = filter_by_model_noise_schedule(model, noise_schedule)
    return schedules


def filter_by_model_noise_schedule(model: Model, noise_schedule: List[NoiseSchedule]) -> List[NoiseSchedule]:
    """
    Filter noise schedule by model
    :param model:
    :param noise_schedule:
    :return:
    """
    # 只有 Novelai4 系列不支持Native
    if model in [
        Model.NAI_DIFFUSION_4_5_CURATED,
        Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING,
        Model.NAI_DIFFUSION_4_5_FULL,
        Model.NAI_DIFFUSION_4_5_FULL_INPAINTING,
        Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
        Model.NAI_DIFFUSION_4_FULL,
        Model.NAI_DIFFUSION_4_FULL_INPAINTING,
        Model.NAI_DIFFUSION_4_CURATED_INPAINTING
    ]:
        return [schedule for schedule in noise_schedule if schedule != NoiseSchedule.NATIVE]
    return noise_schedule


def get_sampler_supported_noise_schedule(sample_type: Sampler) -> List[NoiseSchedule]:
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
    """
    Get model group
    If the model is not in the mapping, return STABLE_DIFFUSION
    :param model: Model enum or model name string
    :return: Model group
    """
    if isinstance(model, str):
        try:
            model = Model(model)
        except ValueError:
            return ModelGroups.STABLE_DIFFUSION
    mapping = {
        Model.STABLE_DIFFUSION: ModelGroups.STABLE_DIFFUSION,
        Model.NAI_DIFFUSION: ModelGroups.STABLE_DIFFUSION,
        Model.SAFE_DIFFUSION: ModelGroups.STABLE_DIFFUSION,
        Model.WAIFU_DIFFUSION: ModelGroups.STABLE_DIFFUSION,
        Model.NAI_DIFFUSION_FURRY: ModelGroups.STABLE_DIFFUSION,
        Model.CURATED_DIFFUSION_TEST: ModelGroups.STABLE_DIFFUSION,
        Model.NAI_DIFFUSION_INPAINTING: ModelGroups.STABLE_DIFFUSION,
        Model.SAFE_DIFFUSION_INPAINTING: ModelGroups.STABLE_DIFFUSION,
        Model.FURRY_DIFFUSION_INPAINTING: ModelGroups.STABLE_DIFFUSION,
        Model.NAI_DIFFUSION_2: ModelGroups.STABLE_DIFFUSION_GROUP_2,
        Model.NAI_DIFFUSION_XL: ModelGroups.STABLE_DIFFUSION_XL,
        Model.NAI_DIFFUSION_3: ModelGroups.STABLE_DIFFUSION_XL,
        Model.NAI_DIFFUSION_3_INPAINTING: ModelGroups.STABLE_DIFFUSION_XL,
        Model.CUSTOM: ModelGroups.V4,
        Model.NAI_DIFFUSION_FURRY_3: ModelGroups.STABLE_DIFFUSION_XL_FURRY,
        Model.NAI_DIFFUSION_FURRY_3_INPAINTING: ModelGroups.STABLE_DIFFUSION_XL_FURRY,
        Model.NAI_DIFFUSION_4_CURATED_PREVIEW: ModelGroups.V4,
        Model.NAI_DIFFUSION_4_FULL: ModelGroups.V4,
        Model.NAI_DIFFUSION_4_FULL_INPAINTING: ModelGroups.V4,
        Model.NAI_DIFFUSION_4_CURATED_INPAINTING: ModelGroups.V4,
        Model.NAI_DIFFUSION_4_5_CURATED: ModelGroups.V4,
        Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING: ModelGroups.V4,
        Model.NAI_DIFFUSION_4_5_FULL: ModelGroups.V4,
        Model.NAI_DIFFUSION_4_5_FULL_INPAINTING: ModelGroups.V4,
    }
    return mapping.get(model, ModelGroups.STABLE_DIFFUSION)


@dataclass
class UcPrompt:
    category: str
    name: str
    text: str


def get_uc_preset(model: ModelTypeAlias) -> List[UcPrompt]:
    prompts: List[UcPrompt] = []
    if model in [
        Model.SAFE_DIFFUSION,
        Model.NAI_DIFFUSION,
        Model.NAI_DIFFUSION_INPAINTING,
        Model.SAFE_DIFFUSION_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="lowQualityPlusBadAnatomy",
                text="nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
            ),
            UcPrompt(
                category="light",
                name="lowQuality",
                text="nsfw, lowres, text, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
            ),
            UcPrompt(
                category="none",
                name="none",
                text="lowres"
            ),
        ]
    elif model in [
        Model.NAI_DIFFUSION_FURRY,
        Model.FURRY_DIFFUSION_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="light",
                name="lowQuality",
                text="nsfw, worst quality, low quality, what has science done, what, nightmare fuel, eldritch horror, where is your god now, why"
            ),
            UcPrompt(
                category="heavy",
                name="badAnatomy",
                text="nsfw, {worst quality}, low quality, distracting watermark, [nightmare fuel], {{unfinished}}, deformed, outline, pattern, simple background"
            ),
            UcPrompt(
                category="none",
                name="none",
                text="low res"
            ),
        ]
    elif model in [
        Model.NAI_DIFFUSION_2,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="heavy",
                text="nsfw, lowres, bad, text, error, missing, extra, fewer, cropped, jpeg artifacts, worst quality, bad quality, watermark, displeasing, unfinished, chromatic aberration, scan, scan artifacts"
            ),
            UcPrompt(
                category="light",
                name="light",
                text="nsfw, lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing"
            ),
            UcPrompt(
                category="none",
                name="none",
                text="lowres"
            ),
        ]
    elif model in [
        Model.NAI_DIFFUSION_3,
        Model.NAI_DIFFUSION_3_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="heavy",
                text="nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract]"
            ),
            UcPrompt(
                category="light",
                name="light",
                text="nsfw, lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing"
            ),
            UcPrompt(
                category="human",
                name="humanFocus",
                text="nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, glowing eyes"
            ),
            UcPrompt(
                category="none",
                name="none",
                text="lowres"
            ),
        ]
    elif model in [
        Model.NAI_DIFFUSION_FURRY_3,
        Model.NAI_DIFFUSION_FURRY_3_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="heavy",
                text="nsfw, {{worst quality}}, [displeasing], {unusual pupils}, guide lines, {{unfinished}}, {bad}, url, artist name, {{tall image}}, mosaic, {sketch page}, comic panel, impact (font), [dated], {logo}, ych, {what}, {where is your god now}, {distorted text}, repeated text, {floating head}, {1994}, {widescreen}, absolutely everyone, sequence, {compression artifacts}, hard translated, {cropped}, {commissioner name}, unknown text, high contrast"
            ),
            UcPrompt(
                category="light",
                name="light",
                text="nsfw, {worst quality}, guide lines, unfinished, bad, url, tall image, widescreen, compression artifacts, unknown text"
            ),
            UcPrompt(
                category="none",
                name="none",
                text="lowres"
            ),
        ]
    elif model in [
        Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
        Model.NAI_DIFFUSION_4_CURATED_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="heavy",
                text="blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, logo, dated, signature, multiple views, gigantic breasts"
            ),
            UcPrompt(
                category="light",
                name="light",
                text="blurry, lowres, error, worst quality, bad quality, jpeg artifacts, very displeasing, logo, dated, signature"
            ),
            UcPrompt(
                category="none",
                name="none",
                text=""
            ),
        ]
    elif model in [
        Model.NAI_DIFFUSION_4_FULL,
        Model.NAI_DIFFUSION_4_FULL_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="heavy",
                text="nsfw, blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, multiple views, logo, too many watermarks, white blank page, blank page"
            ),
            UcPrompt(
                category="light",
                name="light",
                text="nsfw, blurry, lowres, error, worst quality, bad quality, jpeg artifacts, very displeasing, white blank page, blank page"
            ),
            UcPrompt(
                category="none",
                name="none",
                text=""
            ),
        ]
    elif model in [
        Model.CUSTOM,
        Model.NAI_DIFFUSION_4_5_CURATED,
        Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="heavy",
                text="blurry, lowres, upscaled, artistic error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, halftone, multiple views, logo, too many watermarks, negative space, blank page"
            ),
            UcPrompt(
                category="light",
                name="light",
                text="blurry, lowres, upscaled, artistic error, scan artifacts, jpeg artifacts, logo, too many watermarks, negative space, blank page"
            ),
            UcPrompt(
                category="human",
                name="humanFocus",
                text="blurry, lowres, upscaled, artistic error, film grain, scan artifacts, bad anatomy, bad hands, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, halftone, multiple views, logo, too many watermarks, @_@, mismatched pupils, glowing eyes, negative space, blank page"
            ),
            UcPrompt(
                category="none",
                name="none",
                text=""
            ),
        ]
    elif model in [
        Model.NAI_DIFFUSION_4_5_FULL,
        Model.NAI_DIFFUSION_4_5_FULL_INPAINTING,
    ]:
        prompts = [
            UcPrompt(
                category="heavy",
                name="heavy",
                text="nsfw, lowres, artistic error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, dithering, halftone, screentone, multiple views, logo, too many watermarks, negative space, blank page"
            ),
            UcPrompt(
                category="light",
                name="light",
                text="nsfw, lowres, artistic error, scan artifacts, worst quality, bad quality, jpeg artifacts, multiple views, very displeasing, too many watermarks, negative space, blank page"
            ),
            UcPrompt(
                category="furry",
                name="furryFocus",
                text="nsfw, {worst quality}, distracting watermark, unfinished, bad quality, {widescreen}, upscale, {sequence}, {{grandfathered content}}, blurred foreground, chromatic aberration, sketch, everyone, [sketch background], simple, [flat colors], ych (character), outline, multiple scenes, [[horror (theme)]], comic"
            ),
            UcPrompt(
                category="human",
                name="humanFocus",
                text="nsfw, lowres, artistic error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, dithering, halftone, screentone, multiple views, logo, too many watermarks, negative space, blank page, @_@, mismatched pupils, glowing eyes, bad anatomy"
            ),
            UcPrompt(
                category="none",
                name="none",
                text=""
            ),
        ]
    return prompts


def get_default_uc_preset(model: ModelTypeAlias, uc_preset: int) -> str:
    prompts = get_uc_preset(model)
    if 0 <= uc_preset < len(prompts):
        return prompts[uc_preset].text
    else:
        return "lowres"
