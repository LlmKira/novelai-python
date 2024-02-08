# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:57
# @Author  : sudoskys
# @File    : read_nai_tag.py
# @Software: PyCharm
import os

from novelai_python.utils import NovelAiMetadata

if not os.path.exists("generate_image.png"):
    raise FileNotFoundError("generate_image.png not found,pls run generate_image.py first")

ba = NovelAiMetadata.build_from_img(image_io="generate_image.png")
print(ba.title)
print(ba.description)
print(ba.comment)
