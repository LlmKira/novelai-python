# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:57
# @Author  : sudoskys
# @File    : read_nai_tag.py
from pathlib import Path

from novelai_python.tool.image_metadata import ImageMetadata, ImageVerifier

image = Path(__file__).parent.joinpath("sample-0316.png")
image_clear = ImageMetadata.reset_alpha(
    image=image
)

try:
    meta = ImageMetadata.load_image(image)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(meta.Title)
print(f"Description: {meta.Description}")
print(f"Comment: {meta.Comment}")
print(f"Request Method: {meta.Comment.request_type}")
print(f"Used image model: {meta.used_model}")
# Verify if the image is from NovelAI
is_novelai, have_latent = ImageVerifier().verify(image=image)
print(f"Is NovelAI: {is_novelai}")
print(f"Have Latent: {have_latent}")
