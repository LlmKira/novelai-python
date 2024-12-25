import json
from pathlib import Path

from PIL import Image
from loguru import logger

"""
   Read the metadata from the image using raw PIL
   To conveniently read the metadata from the image, check read_image_nai_tag.py
"""

image_io = Path(__file__).parent.joinpath("sample-0316.png")
with Image.open(image_io) as img:
    title = img.info.get("Title", None)
    prompt = img.info.get("Description", None)
    comment = img.info.get("Comment", None)
    print(img.info)

    assert isinstance(comment, str), ValueError("Comment Empty")
    try:
        comment = json.loads(comment)
    except Exception as e:
        logger.debug(e)
        comment = {}
print(title)
print(prompt)
print(comment)

"""
AI generated image
1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres, rating:general, amazing quality, very aesthetic, absurdres
{'prompt': '1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres, rating:general, amazing quality, very aesthetic, absurdres', 'steps': 23, 'height': 1216, 'width': 832, 'scale': 6.0, 'uncond_scale': 0.0, 'cfg_rescale': 0.0, 'seed': 3685348292, 'n_samples': 1, 'noise_schedule': 'karras', 'legacy_v3_extend': False, 'reference_information_extracted_multiple': [], 'reference_strength_multiple': [], 'extra_passthrough_testing': {'prompt': None, 'uc': None, 'hide_debug_overlay': False, 'r': 0.0, 'eta': 1.0, 'negative_momentum': 0.0}, 'v4_prompt': {'caption': {'base_caption': '1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres, rating:general, amazing quality, very aesthetic, absurdres', 'char_captions': [{'char_caption': '1girl', 'centers': [{'x': 0.0, 'y': 0.0}]}, {'char_caption': '1boy', 'centers': [{'x': 0.9, 'y': 0.9}]}]}, 'use_coords': True, 'use_order': True}, 'v4_negative_prompt': {'caption': {'base_caption': 'lowres', 'char_captions': [{'char_caption': 'red hair', 'centers': [{'x': 0.0, 'y': 0.0}]}, {'char_caption': '', 'centers': [{'x': 0.9, 'y': 0.9}]}]}, 'use_coords': False, 'use_order': False}, 'sampler': 'k_euler_ancestral', 'controlnet_strength': 1.0, 'controlnet_model': None, 'dynamic_thresholding': False, 'dynamic_thresholding_percentile': 0.999, 'dynamic_thresholding_mimic_scale': 10.0, 'sm': False, 'sm_dyn': False, 'skip_cfg_above_sigma': None, 'skip_cfg_below_sigma': 0.0, 'lora_unet_weights': None, 'lora_clip_weights': None, 'deliberate_euler_ancestral_bug': False, 'prefer_brownian': True, 'cfg_sched_eligibility': 'enable_for_post_summer_samplers', 'explike_fine_detail': False, 'minimize_sigma_inf': False, 'uncond_per_vibe': True, 'wonky_vibe_correlation': True, 'version': 1, 'uc': 'lowres', 'request_type': 'PromptGenerateRequest', 'signed_hash': 'usuVOlHJg8QFGj4nXAkC7iWKlemqttUcuvjtvGRtPzBZWiHwa/XrcM3p928gsz0F97JMb70YoVYvBG+Cbtu/Bw=='}
"""
