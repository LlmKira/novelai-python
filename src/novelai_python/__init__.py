# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午12:18
# @Author  : sudoskys
# @File    : __init__.py
from ._exceptions import (
    NovelAiError,
    APIError,
    AuthError,
    ConcurrentGenerationError,
    SessionHttpError
)
from .credential import JwtCredential, LoginCredential, ApiCredential
from .sdk import AugmentImageInfer
from .sdk import GenerateImageInfer, ImageGenerateResp
from .sdk import Information, InformationResp
from .sdk import LLM, LLMResp
from .sdk import LLMStream, LLMStreamResp
from .sdk import Login, LoginResp
from .sdk import Subscription, SubscriptionResp
from .sdk import SuggestTags, SuggestTagsResp
from .sdk import Upscale, UpscaleResp
from .sdk import VoiceGenerate, VoiceResponse

__all__ = [
    "LLM",
    "LLMResp",

    "LLMStream",
    "LLMStreamResp",

    "GenerateImageInfer",
    "ImageGenerateResp",

    "AugmentImageInfer",

    "VoiceGenerate",
    "VoiceResponse",

    "Upscale",
    "UpscaleResp",

    "Subscription",
    "SubscriptionResp",

    "Login",
    "LoginResp",

    "SuggestTags",
    "SuggestTagsResp",

    "Information",
    "InformationResp",

    "JwtCredential",
    "LoginCredential",
    "ApiCredential",

    "APIError",
    "SessionHttpError",
    "AuthError",
    "NovelAiError",
    "ConcurrentGenerationError"
]
