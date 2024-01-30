# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午10:51
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import io
import json
from typing import Union

from loguru import logger

from .hash import NovelAiMetadata


def png_info_reset(img: Union[str, io.BytesIO]):
    """
    reset png info hash value
    :param img: BytesIO 对象
    :return: 
    """
    _fixed = NovelAiMetadata.rehash(img_io=img)
    return _fixed


def try_jsonfy(obj: Union[str, dict, list, tuple]):
    """
    try to jsonfy a object
    :param obj:
    :return:
    """
    try:
        return json.loads(obj)
    except Exception:
        logger.error(f"Decode Error {obj}")
        return f"Decode Error {type(obj)}"
