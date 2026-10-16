# @Time    : 2024/1/26 上午10:51
# @Author  : sudoskys
# @File    : __init__.py.py

import json

from loguru import logger

from .encode import encode_access_key


def try_jsonfy(obj: str | dict | list | tuple, default_when_error=None):
    """
    try to jsonfy object
    :param obj:
    :param default_when_error:
    :return:
    """
    try:
        return json.loads(obj)
    except Exception as e:
        logger.trace(f"Decode Error {obj} {e}")
        if default_when_error is None:
            return f"Decode Error {type(obj)}"
        else:
            return default_when_error
