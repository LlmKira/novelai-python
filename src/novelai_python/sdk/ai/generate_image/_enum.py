# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:10
# @Author  : sudoskys
# @File    : _enum.py
# @Software: PyCharm
from enum import Enum, IntEnum


class Sampler(Enum):
    K_EULER = "k_euler"
    K_EULER_ANCESTRAL = "k_euler_ancestral"
    K_DPMPP_2S_ANCESTRAL = "k_dpmpp_2s_ancestral"
    K_DPMPP_2M = "k_dpmpp_2m"
    K_DPMPP_SDE = "k_dpmpp_sde"
    DDIM_V3 = "ddim_v3"

    DDIM = "ddim"
    PLMS = "plms"
    K_DPM_2 = "k_dpm_2"
    K_DPM_2_ANCESTRAL = "k_dpm_2_ancestral"
    K_LMS = "k_lms"
    K_DPM_ADAPTIVE = "k_dpm_adaptive"
    K_DPM_FAST = "k_dpm_fast"
    K_DPMPP_2M_SDE = "k_dpmpp_2m_sde"
    K_DPMPP_3M_SDE = "k_dpmpp_3m_sde"
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

    NAI_DIFFUSION = "nai-diffusion"
    NAI_DIFFUSION_2 = "nai-diffusion-2"
    NAI_DIFFUSION_INPAINTING = "nai-diffusion-inpainting"

    SAFE_DIFFUSION = "safe-diffusion"
    SAFE_DIFFUSION_INPAINTING = "safe-diffusion-inpainting"

    NAI_DIFFUSION_FURRY = "nai-diffusion-furry"
    # NAI_DIFFUSION_FURRY2 = "nai-diffusion-furry2"
    FURRY_DIFFUSION_INPAINTING = "furry-diffusion-inpainting"

    CUSTOM = "custom"


INPAINTING_MODEL_LIST = [Model.NAI_DIFFUSION_3_INPAINTING,
                         Model.NAI_DIFFUSION_INPAINTING,
                         Model.SAFE_DIFFUSION_INPAINTING,
                         Model.FURRY_DIFFUSION_INPAINTING
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
    "Stable Diffusion XL 8BA2AF87": Model.NAI_DIFFUSION_3,
}
