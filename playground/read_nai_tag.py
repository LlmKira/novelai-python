# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:57
# @Author  : sudoskys
# @File    : read_nai_tag.py
# @Software: PyCharm
import os

from novelai_python.utils import NovelAIMetadata

if not os.path.exists("generate_image.png"):
    raise FileNotFoundError("generate_image.png not found,pls run generate_image.py first")
try:
    meta = NovelAIMetadata.build_from_img(image_io="generate_image.png")  # OR BytesIO(data)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(meta.title)
print(meta.description)
print(meta.comment)
