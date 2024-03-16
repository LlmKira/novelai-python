from pathlib import Path

from PIL import Image
import json
from io import BytesIO
from loguru import logger

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
 silvery white, best quality, amazing quality, very aesthetic, absurdres
{'prompt': ' silvery white, best quality, amazing quality, very aesthetic, absurdres', 'steps': 28, 'height': 128, 'width': 128, 'scale': 10.0, 'uncond_scale': 1.0, 'cfg_rescale': 0.38, 'seed': 1148692016, 'n_samples': 1, 'hide_debug_overlay': False, 'noise_schedule': 'native', 'legacy_v3_extend': False, 'reference_information_extracted': 0.87, 'reference_strength': 1.0, 'sampler': 'k_euler', 'controlnet_strength': 1.0, 'controlnet_model': None, 'dynamic_thresholding': False, 'dynamic_thresholding_percentile': 0.999, 'dynamic_thresholding_mimic_scale': 10.0, 'sm': True, 'sm_dyn': True, 'skip_cfg_below_sigma': 0.0, 'lora_unet_weights': None, 'lora_clip_weights': None, 'uc': 'nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], small', 'request_type': 'PromptGenerateRequest', 'signed_hash': 'GmLfTgQTOI4WRcTloiSmenArH/Y8szJdVJ1DW18yeqYPkqw3o1zellB4xCQFYle+0tuF9KVP8RkHiDNbQXr0DA=='}
"""
