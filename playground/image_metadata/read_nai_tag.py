# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:57
# @Author  : sudoskys
# @File    : read_nai_tag.py
from io import BytesIO
from pathlib import Path

from novelai_python.tool.image_metadata import ImageMetadata

image = Path(__file__).parent.joinpath("sample-0316.png")
image_clear = ImageMetadata.reset_alpha(
    input_img=BytesIO(image.read_bytes())
)

try:
    meta = ImageMetadata.load_image(image)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(meta.Title)
print(meta.Description)
print(meta.Comment)

try:
    meta = ImageMetadata.load_image(image_clear)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(meta.Title)
print(meta.Description)
print(meta.Comment)

image = Path(__file__).parent.joinpath("sample-0317.png")
try:
    meta = ImageMetadata.load_image(image)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(meta.Title)
print(meta.Description)
print(meta.Comment)
