# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午1:58
# @Author  : sudoskys
# @File    : enhance.py

from loguru import logger
import random
from typing import Tuple
from novelai_python.sdk.ai.generate_image import Model, Params, UCPreset, Sampler
from novelai_python.sdk.ai._enum import get_supported_params

# NOTE About Enhance Mode
# Enhance Mode = origin model name + img2img action + width *1.5(or 1) +height *1.5(or 1) + !!diff seed!!
# :)
logger.info("Enhance Mode = origin model name + img2img action + width *1.5(or 1) +height *1.5(or 1) + diff seed")
logger.warning("If you use the nai-generated image as input, please diff the seed!")


async def enhance_image(
    model: Model,
    original_image: bytes,
    original_width: int,
    original_height: int,
    prompt: str,
    enhance_scale: float = 1.5,
    enhance_strength: float = 0.7,
    enhance_noise: float = 0.1,
    quality_toggle: bool = True,
    uc_preset: UCPreset = UCPreset.TYPE0,
    character_prompts: list = None,
) -> Tuple[str, Params]:
    """
    Generate enhanced image with novelai api
    
    Args:
        model: The model to use
        original_image: The original image data
        original_width: The original image width
        original_height: The original image height
        prompt: The prompt
        enhance_scale: The enhance scale, default 1.5
        enhance_strength: The enhance strength, default 0.7
        enhance_noise: The enhance noise, default 0.1
        quality_toggle: Whether to enable quality toggle
        uc_preset: UC preset
        character_prompts: The character prompts list
    
    Returns:
        Tuple[str, Params]: The processed prompt and parameters
    """
    # Calculate new size
    new_width = int(original_width * enhance_scale)
    new_height = int(original_height * enhance_scale)
    
    # Base parameters setting
    params = Params(
        width=new_width,
        height=new_height,
        n_samples=1,
        image=original_image,  # base64 encoded image
        strength=enhance_strength,
        noise=enhance_noise,
        seed=random.randint(0, 4294967295 - 7),  # Use different seed
        character_prompts=character_prompts or [],
        quality_toggle=quality_toggle,
        uc_preset=uc_preset,
        sampler=Sampler.K_EULER_ANCESTRAL,
    )
    
    # Process prompt
    final_prompt = prompt
    if get_supported_params(model).enhancePromptAdd and "upscaled, blurry" not in prompt:
        # Add negative prompt
        negative_prompt = ", -2::upscaled, blurry::,"
        # Insert negative prompt after the first comma
        if "," in prompt:
            parts = prompt.split(",", 1)
            final_prompt = parts[0] + negative_prompt + "," + parts[1]
        else:
            final_prompt += negative_prompt
    
    return final_prompt, params


# Example usage
async def example_usage():
    """
    Example usage of enhance mode
    """
    # Assume we have an original image
    with open("original.png", "rb") as f:
        original_image = f.read()
    
    # Call enhance function
    prompt, params = await enhance_image(
        model=Model.NAI_DIFFUSION_4_5_CURATED,
        original_image=original_image,
        original_width=832,
        original_height=1216,
        prompt="1girl, masterpiece, best quality",
        enhance_scale=1.5,
        enhance_strength=0.7,
        enhance_noise=0.1,
    )
    
    logger.info(f"Enhanced prompt: {prompt}")
    logger.info(f"Enhanced params: {params}")
