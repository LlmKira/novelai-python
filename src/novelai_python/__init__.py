# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午12:18
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm

from ._exceptions import (
    NovelAiError,
    APIError,
    AuthError,
    ConcurrentGenerationError,
    SessionHttpError
)
from .credential import JwtCredential, LoginCredential, ApiCredential
from .sdk import GenerateImageInfer, ImageGenerateResp
from .sdk import SuggestTags, SuggestTagsResp
from .sdk import Information, InformationResp
from .sdk import Login, LoginResp
from .sdk import Subscription, SubscriptionResp
from .sdk import Upscale, UpscaleResp

__all__ = [
    "GenerateImageInfer",
    "ImageGenerateResp",

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
