# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:57
# @Author  : sudoskys
# @File    : read_nai_tag.py
from pathlib import Path

from PIL import Image

from novelai_python.tool.image_metadata import ImageMetadata, ImageVerifier

image = Path(__file__).parent.joinpath("sample-0316.png")
with Image.open(image) as img:
    image_clear = ImageMetadata.reset_alpha(
        image=img,
    )

try:
    with Image.open(image) as img:
        meta_auto = ImageMetadata.load_image(img)
        meta1 = ImageMetadata.load_from_watermark(img)
        meta2 = ImageMetadata.load_from_pnginfo(img)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(meta1.Generation_time)  # Meatadata from watermark have no Generation_time...
print(meta2.Generation_time)
print(f"Description: {meta_auto.Description}")
print(f"Comment: {meta_auto.Comment}")
print(f"Request Method: {meta_auto.Comment.request_type}")
print(f"Used image model: {meta_auto.used_model}")
# Verify if the image is from NovelAI
with Image.open(image) as img:
    is_novelai, have_latent = ImageVerifier().verify(image=img)
print(f"Is NovelAI: {is_novelai}")
print(f"Have Latent: {have_latent}")
