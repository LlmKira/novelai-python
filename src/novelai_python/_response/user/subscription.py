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
    contextTokens: int
    # optional: current responses leave these out, older payloads still carry them
    voiceGeneration: bool | None = None
    imageGeneration: bool | None = None
    unlimitedImageGeneration: bool | None = None
    unlimitedImageGenerationLimits: list[ImageGenerationLimit] | None = None


class SubscriptionUsage(BaseModel):
    """Opus usage limit for NovelAI Diffusion V5. The bar refills continuously: ``timeUntilNextPercent`` is the
    PERIOD in seconds per +1 % (the web client derives "%/day" as
    86400 / timeUntilNextPercent), not a countdown. While ``isNegative`` is
    false, V5 generations at normal resolution / <= 28 steps are free; once the
    bar is below zero every V5 generation costs Anlas until it refills."""

    percent: int = Field(default=0, description="Usage bar level, may exceed 100 after bonuses")
    purchasedPercent: int = Field(default=0, description="Bought extra usage on top of the bar, 0-300 %")
    isNegative: bool = Field(default=False, description="Bar is below zero: V5 now costs Anlas")
    timeUntilNextPercent: int | None = Field(
        default=None, description="Seconds per +1 %; 0 while the refill is paused above the cap"
    )

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
    usage: SubscriptionUsage | None = Field(default=None, description="Opus V5 usage bar (absent on non-Opus)")
    paymentProcessor: str | None = Field(default=None, description='e.g. "chargebee"')
    isGracePeriod: bool | None = None
    isPaypal: bool | None = None
    isNewCustomer: bool | None = None

    @property
    def is_active(self):
        return self.active

    @property
    def anlas_left(self):
        return self.trainingStepsLeft.fixedTrainingStepsLeft + self.trainingStepsLeft.purchasedTrainingSteps

    @property
    def is_unlimited_image_generation(self) -> bool:
        if self.perks.unlimitedImageGeneration is None:
            # current API: Opus image generation is metered by the usage bar instead of a perk flag
            return self.usage is not None and not self.usage.isNegative
        return bool(self.perks.unlimitedImageGeneration and self.perks.imageGeneration)

    @property
    def get_tier_name(self) -> str:
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
        if self.perks.imageGeneration is False:
            perks.append("imageGeneration")
        if self.perks.voiceGeneration is False:
            perks.append("voiceGeneration")
        if self.perks.unlimitedImageGeneration is False:
            perks.append("unlimitedImageGeneration")
        if not self.perks.unlimitedMaxPriority:
            perks.append("unlimitedMaxPriority")
        return perks
