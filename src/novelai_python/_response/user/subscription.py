# @Time    : 2024/2/7 上午9:57
# @Author  : sudoskys
# @File    : subscription.py

from typing import Any

from pydantic import BaseModel, Field

from ..schema import RespBase


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
    unlimitedImageGenerationLimits: list[ImageGenerationLimit]
    contextTokens: int


class SubscriptionUsage(BaseModel):
    """Opus usage limit for NovelAI Diffusion V5 (introduced with the V5 release,
    2026-08). The bar refills continuously: ``timeUntilNextPercent`` is the
    PERIOD in seconds per +1 % (the web client derives "%/day" as
    86400 / timeUntilNextPercent), not a countdown. While ``isNegative`` is
    false, V5 generations at normal resolution / <= 28 steps are free; once the
    bar is below zero every V5 generation costs Anlas until it refills."""

    percent: int = Field(0, description="Usage bar level, may exceed 100 after bonuses")
    isNegative: bool = Field(False, description="Bar is below zero: V5 now costs Anlas")
    timeUntilNextPercent: int | None = Field(None, description="Seconds per +1 %")

    @property
    def refill_percent_per_day(self) -> float | None:
        if not self.timeUntilNextPercent:
            return None
        return 86400 / self.timeUntilNextPercent

    @property
    def images_left_estimate(self) -> int:
        """Web client constant: ~17.3 default-settings images per 1 %."""
        return 0 if self.isNegative else int(self.percent * 17.3)


class SubscriptionResp(RespBase):
    tier: int = Field(..., description="Subscription tier")
    active: bool = Field(..., description="Subscription status")
    expiresAt: int = Field(..., description="Subscription expiration time")
    perks: Perks = Field(..., description="Subscription perks")
    paymentProcessorData: dict[Any, Any] | None
    trainingStepsLeft: TrainingSteps = Field(..., description="Training steps left")
    accountType: int = Field(..., description="Account type")
    usage: SubscriptionUsage | None = Field(None, description="Opus V5 usage bar (absent on non-Opus)")

    @property
    def is_active(self):
        return self.active

    @property
    def anlas_left(self):
        return self.trainingStepsLeft.fixedTrainingStepsLeft + self.trainingStepsLeft.purchasedTrainingSteps

    @property
    def is_unlimited_image_generation(self):
        return self.perks.unlimitedImageGeneration and self.perks.imageGeneration

    @property
    def get_tier_name(self):
        if self.tier == 0:
            return "Paper"
        elif self.tier == 1:
            return "Tablet"
        elif self.tier == 2:
            return "Scroll"
        elif self.tier == 3:
            return "Opus"
        else:
            return "Unknown"

    @property
    def limit_perks(self):
        perks = []
        if not self.perks.imageGeneration:
            perks.append("imageGeneration")
        if not self.perks.voiceGeneration:
            perks.append("voiceGeneration")
        if not self.perks.unlimitedImageGeneration:
            perks.append("unlimitedImageGeneration")
        if not self.perks.unlimitedMaxPriority:
            perks.append("unlimitedMaxPriority")
        return perks
