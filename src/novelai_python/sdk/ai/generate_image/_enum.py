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
    M_LSD = "mlsd"
    """(建筑)线条检测"""
    LANDSCAPER = "uniformer"
    """风景生成"""


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
    NAI_DIFFUSION_INPAINTING = "nai-diffusion-inpainting"

    SAFE_DIFFUSION = "safe-diffusion"
    SAFE_DIFFUSION_INPAINTING = "safe-diffusion-inpainting"

    NAI_DIFFUSION_FURRY = "nai-diffusion-furry"
    FURRY_DIFFUSION_INPAINTING = "furry-diffusion-inpainting"
