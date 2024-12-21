import math
import random
from typing import List, Optional

from pydantic import BaseModel

from novelai_python.sdk.ai._const import map, initialN, initial_n, step, newN
from novelai_python.sdk.ai._enum import Sampler, ModelGroups, get_model_group, ModelTypeAlias


class Args(BaseModel):
    height: int
    width: int
    image: bool
    n_samples: int
    strength: Optional[float]
    steps: int
    sm: bool
    sm_dyn: bool
    sampler: Optional[Sampler] = None
    tool: Optional[str] = None
    defry: int = 0
    extra: str = ""


def generate_random_seed() -> int:
    return random.randint(0, 2 ** 32 - 1)


class CostCalculator:

    @staticmethod
    def calculate(
            width: int,
            height: int,
            steps: int,
            image: bool,
            n_samples: int,
            account_tier: int,
            strength: Optional[float],
            is_sm_enabled: bool,
            is_sm_dynamic: bool,
            is_account_active: bool,
            sampler: Optional[Sampler],
            model: ModelTypeAlias,
            tool: str = None,
            is_tool_active: bool = False
    ) -> int:
        return CostCalculator.calculate_cost(
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
                tool=tool
            ),
            model_group=get_model_group(model) if model else None,
            is_account_active=is_account_active,
            account_tier=account_tier,
            is_tool_active=is_tool_active
        )

    @staticmethod
    def calculate_cost(
            params: Args,
            *,
            is_account_active: bool,
            account_tier: int,
            model_group: ModelGroups = None,
            is_tool_active: bool = False) -> int:
        def calculate_steps_cost(width: int,
                                 height: int,
                                 steps: int) -> float:
            multiplier = width * height
            return (15.266497014243718 * math.exp(
                multiplier / 1048576 * 0.6326248927474729) - 15.225164493059737) / 28 * steps

        def calculate_dimension_cost(width: int,
                                     height: int,
                                     steps: int,
                                     is_sm_enabled: bool,
                                     is_sm_dynamic: bool) -> int:
            multiplier = width * height
            factor = 1.4 if is_sm_dynamic else 1.2 if is_sm_enabled else 1
            return math.ceil(2951823174884865e-21 * multiplier + 5.753298233447344e-7 * multiplier * steps) * factor

        def calculate_sampling_cost(width: int,
                                    height: int,
                                    steps: int,
                                    sampler_type: Optional[Sampler],
                                    is_sm_enabled: bool,
                                    is_sm_dynamic: bool) -> int:
            sampling_factor: List[int]
            if sampler_type == Sampler.K_EULER_ANCESTRAL:
                sampling_factor = step
            elif sampler_type == Sampler.NAI_SMEA:
                sampling_factor = newN
            elif sampler_type == Sampler.NAI_SMEA_DYN:
                sampling_factor = initialN
            elif sampler_type == Sampler.DDIM:
                sampling_factor = initial_n
            else:
                sampling_factor = step

            if is_sm_dynamic:
                sampling_factor = initialN
            elif is_sm_enabled:
                sampling_factor = newN

            def prepare_array() -> List[int]:
                result_array: List[int] = []
                map_iterator = enumerate(map)
                try:
                    for key, value in map_iterator:
                        # 确保 result_array 的大小足够大
                        while len(result_array) <= value:
                            result_array.append(0)
                        result_array[value] = 2 * key
                except Exception as error:
                    # 处理错误（如果有必要）
                    raise error
                return result_array

            index = prepare_array()[math.floor(width / 64) * math.floor(height / 64)]
            return (sampling_factor[index] if index < len(sampling_factor) else 0) * steps + (
                sampling_factor[index + 1] if index + 1 < len(sampling_factor) else 0)

        img_height = params.height
        img_width = params.width
        dimension = img_width * img_height
        if dimension < 65536:
            dimension = 65536

        base_dimension = 1048576
        strength_multiplier = params.strength if (isinstance(params.strength, float) and params.image) else 1
        steps = params.steps
        samples = params.n_samples

        if steps <= 28 and dimension <= base_dimension and account_tier >= 3 and is_account_active and not is_tool_active:
            samples -= 1

        if model_group and model_group in [ModelGroups.STABLE_DIFFUSION_XL, ModelGroups.STABLE_DIFFUSION_XL_FURRY,
                                           ModelGroups.V4]:
            cost = calculate_dimension_cost(img_width, img_height, steps, params.sm, params.sm_dyn)
        elif dimension <= base_dimension and params.sampler in [
            Sampler.PLMS, Sampler.DDIM,
            Sampler.K_EULER, Sampler.K_EULER_ANCESTRAL,
            Sampler.K_LMS
        ]:
            cost = calculate_steps_cost(img_width, img_height, steps)
        else:
            cost = calculate_sampling_cost(img_width, img_height, steps, params.sampler, params.sm, params.sm_dyn)

        final_cost = max(math.ceil(cost * strength_multiplier), 2)
        if final_cost > 140:
            return -3

        return final_cost * samples
