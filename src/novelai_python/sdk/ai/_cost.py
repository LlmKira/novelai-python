"""
Anlas cost of image requests, as the novelai.net web client computes it
(checkStableDiffusionPrice, checkUpscalePrice and the image tools price hook).
"""

import math
import random

from pydantic import BaseModel

from novelai_python.sdk.ai._const import initial_n, initialN, map, newN, step
from novelai_python.sdk.ai._enum import (
    Model,
    ModelGroups,
    ModelTypeAlias,
    Sampler,
    as_model,
    get_model_group,
)

ANLAS_MAX = 140
"""A single image above this price is refused (-3)."""
OPUS_FREE_PIXELS = 1048576
OPUS_FREE_STEPS = 28
TOOL_MAX_PIXELS = 3145728
"""Image tools scale the billed area into [OPUS_FREE_PIXELS, TOOL_MAX_PIXELS]."""
UPSCALE_PRICES = [(1048576, 1), (1747627, 2), (2446678, 3), (3145728, 4)]
CHARACTER_REFERENCE_PRICE = 5
"""Per character reference and per image, on top of the generation."""

# V5 Full / Curated draw from the Opus usage bar; the free generation stops while it is negative.
_OPUS_USAGE_LIMIT_MODELS = {
    Model.CUSTOM,
    Model.NAI_DIFFUSION_5_FULL,
    Model.NAI_DIFFUSION_5_FULL_MEDIUM,  # the web client spreads V5 Full's capabilities
    Model.NAI_DIFFUSION_5_FULL_MEDIUM_INPAINTING,
    Model.NAI_DIFFUSION_5_FULL_INPAINTING,
    Model.NAI_DIFFUSION_5_CURATED,
    Model.NAI_DIFFUSION_5_CURATED_INPAINTING,
}
_MEDIUM_STEP_FACTOR = {
    Model.NAI_DIFFUSION_5_FULL_MEDIUM: 1 / 1.06521739,
    Model.NAI_DIFFUSION_5_FULL_MEDIUM_INPAINTING: 1 / 1.06521739,
}


class Args(BaseModel):
    height: int
    width: int
    image: bool
    n_samples: int
    strength: float | None
    steps: int
    sm: bool
    sm_dyn: bool
    sampler: Sampler | None = None
    tool: str | None = None
    defry: int = 0
    extra: str = ""
    mask: bool = False
    inpaint_strength: float | None = None


def generate_random_seed() -> int:
    return random.randint(0, 2**32 - 1)


def _resize_within(width: int, height: int, max_pixels: int) -> tuple[int, int]:
    if width * height <= max_pixels:
        return width, height
    factor = math.sqrt(max_pixels / (width * height))
    return math.floor(width * factor), math.floor(height * factor)


def _resize_up_to(width: int, height: int, min_pixels: int) -> tuple[int, int]:
    if width * height >= min_pixels:
        return width, height
    factor = math.sqrt(min_pixels / (width * height))
    return math.floor(width * factor), math.floor(height * factor)


class CostCalculator:
    @staticmethod
    def calculate(
        width: int,
        height: int,
        steps: int,
        image: bool,
        n_samples: int,
        account_tier: int,
        strength: float | None,
        is_sm_enabled: bool,
        is_sm_dynamic: bool,
        is_account_active: bool,
        sampler: Sampler | None,
        model: ModelTypeAlias,
        tool: str | None = None,
        is_tool_active: bool = False,
        *,
        mask: bool = False,
        inpaint_strength: float | None = None,
        usage_negative: bool = False,
        character_references: int = 0,
        vibe_references: int = 0,
    ) -> int:
        """
        Anlas for one generate-image request.

        :param character_references: number of character reference images (+5 each per image).
        :param vibe_references: number of enabled vibe references; more than four cost 2 each.
            Encoding a new vibe is billed by EncodeVibe, not here.
        :param usage_negative: the Opus usage bar is below zero (``SubscriptionUsage.isNegative``);
            V5 Full / Curated are not free then.
        :param is_tool_active: the request is a background removal, which is never free.
        :return: the price, or -3 when one image would cost more than ANLAS_MAX.
        """
        price = CostCalculator.calculate_cost(
            Args(
                height=height,
                width=width,
                image=image,
                n_samples=n_samples,
                strength=strength,
                steps=steps,
                sm=is_sm_enabled,
                sm_dyn=is_sm_dynamic,
                sampler=sampler,
                tool=tool,
                mask=mask,
                inpaint_strength=inpaint_strength,
            ),
            model=model,
            is_account_active=is_account_active,
            account_tier=account_tier,
            is_tool_active=is_tool_active or tool == "bg-removal",
            usage_negative=usage_negative,
        )
        if price < 0:
            return price
        return price + CHARACTER_REFERENCE_PRICE * character_references * n_samples + 2 * max(0, vibe_references - 4)

    @staticmethod
    def calculate_cost(
        params: Args,
        *,
        is_account_active: bool,
        account_tier: int,
        model_group: ModelGroups | None = None,
        model: ModelTypeAlias = None,
        is_tool_active: bool = False,
        usage_negative: bool = False,
    ) -> int:
        model = as_model(model)
        if model_group is None and model is not None:
            model_group = get_model_group(model)
        width, height, steps = params.width, params.height, params.steps
        pixels = width * height

        if params.mask:
            strength = params.inpaint_strength if params.inpaint_strength is not None else 1
        elif params.image and params.strength is not None:
            strength = params.strength
        else:
            strength = 1

        samples = params.n_samples
        # A character reference keeps the generation itself free: a live V4.5 request with one
        # reference cost 5 Anlas on Opus, the reference surcharge alone.
        opus_free = pixels <= OPUS_FREE_PIXELS and steps <= OPUS_FREE_STEPS
        bar_blocks = model in _OPUS_USAGE_LIMIT_MODELS and usage_negative
        if opus_free and account_tier >= 3 and is_account_active and not bar_blocks and not is_tool_active:
            samples -= 1

        if model_group in (
            ModelGroups.STABLE_DIFFUSION_XL,
            ModelGroups.STABLE_DIFFUSION_XL_FURRY,
            ModelGroups.V4,
            ModelGroups.V5,
        ):
            step_factor = _MEDIUM_STEP_FACTOR.get(model, 1) if isinstance(model, Model) else 1
            smea = 1.4 if params.sm and params.sm_dyn else 1.2 if params.sm else 1
            cost = math.ceil(2951823174884865e-21 * pixels + 5753298233447344e-22 * pixels * steps * step_factor) * smea
        elif max(pixels, 65536) <= OPUS_FREE_PIXELS and params.sampler in (
            Sampler.PLMS,
            Sampler.DDIM,
            Sampler.K_EULER,
            Sampler.K_EULER_ANCESTRAL,
            Sampler.K_LMS,
        ):
            cost = (
                (15.266497014243718 * math.exp(pixels / 1048576 * 0.6326248927474729) - 15.225164493059737) / 28 * steps
            )
        else:
            cost = CostCalculator._sampling_cost(width, height, steps, params.sampler, params.sm, params.sm_dyn)
        if model_group == ModelGroups.V5:
            cost *= 1.5

        final_cost = max(math.ceil(cost * strength), 2)
        if final_cost > ANLAS_MAX:
            return -3
        return final_cost * samples

    @staticmethod
    def _sampling_cost(width: int, height: int, steps: int, sampler: Sampler | None, sm: bool, sm_dyn: bool) -> float:
        if sm and sm_dyn:
            table = initialN
        elif sm or sampler == Sampler.NAI_SMEA:
            table = newN
        elif sampler == Sampler.NAI_SMEA_DYN:
            table = initialN
        elif sampler == Sampler.DDIM:
            table = initial_n
        else:
            table = step
        positions: list[int] = []
        for key, value in enumerate(map):
            while len(positions) <= value:
                positions.append(0)
            positions[value] = 2 * key
        index = positions[math.floor(width / 64) * math.floor(height / 64)]
        return (table[index] if index < len(table) else 0) * steps + (table[index + 1] if index + 1 < len(table) else 0)

    @staticmethod
    def calculate_tool(
        tool: str,
        width: int,
        height: int,
        *,
        account_tier: int = 1,
        is_account_active: bool = True,
    ) -> int:
        """
        Anlas for a Director Tools request (``/ai/augment-image``) or ``/ai/upscale``.

        The web client bills a tool as a V3 generation at 28 steps after scaling the image into
        1-3 MP; background removal costs three times that plus 5 and is never free, pixel snap
        is free, and upscale takes images up to 1 MP.

        :return: the price; -2 when the tool does not take an image this large, -3 above ANLAS_MAX.
        """
        if tool == "pixel-snap":
            return 0
        if tool == "upscale":
            if width * height > OPUS_FREE_PIXELS:
                return -2
            return next((price for limit, price in UPSCALE_PRICES if width * height <= limit), -3)
        width, height = _resize_within(width, height, TOOL_MAX_PIXELS)
        width, height = _resize_up_to(width, height, OPUS_FREE_PIXELS)
        bg_removal = tool == "bg-removal"
        price = CostCalculator.calculate_cost(
            Args(width=width, height=height, image=False, n_samples=1, strength=None, steps=28, sm=False, sm_dyn=False),
            model=Model.NAI_DIFFUSION_3,
            account_tier=account_tier,
            is_account_active=is_account_active,
            is_tool_active=bg_removal,
        )
        if bg_removal and price >= 0:
            price = 3 * price + 5
        return price
