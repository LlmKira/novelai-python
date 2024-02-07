# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午9:57
# @Author  : sudoskys
# @File    : subscription.py
# @Software: PyCharm
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class TrainingSteps(BaseModel):
    fixedTrainingStepsLeft: int
    purchasedTrainingSteps: int


class ImageGenerationLimit(BaseModel):
    resolution: int
    maxPrompts: int


class Perks(BaseModel):
    maxPriorityActions: int
    startPriority: int
    moduleTrainingSteps: int
    unlimitedMaxPriority: bool
    voiceGeneration: bool
    imageGeneration: bool
    unlimitedImageGeneration: bool
    unlimitedImageGenerationLimits: List[ImageGenerationLimit]
    contextTokens: int


class SubscriptionResp(BaseModel):
    tier: int = Field(..., description="Subscription tier")
    active: bool = Field(..., description="Subscription status")
    expiresAt: int = Field(..., description="Subscription expiration time")
    perks: Perks = Field(..., description="Subscription perks")
    paymentProcessorData: Optional[Dict[Any, Any]]
    trainingStepsLeft: TrainingSteps = Field(..., description="Training steps left")
    accountType: int = Field(..., description="Account type")

    @property
    def is_active(self):
        return self.active

    @property
    def anlas_left(self):
        return self.trainingStepsLeft.fixedTrainingStepsLeft

    @property
    def is_unlimited_image_generation(self):
        return self.perks.unlimitedImageGeneration
