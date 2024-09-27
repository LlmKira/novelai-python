# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:57
# @Author  : sudoskys
# @File    : read_nai_tag.py
from pathlib import Path

from novelai_python.tool.image_metadata import ImageMetadata

image = Path(__file__).parent.joinpath("sample-2.png")
image_clear = ImageMetadata.reset_alpha(
    image=image
)

try:
    meta = ImageMetadata.load_image(image)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(meta.Title)
print(meta.Description)
print(meta.Comment)
print(ImageMetadata.verify_image_is_novelai(image=image))
