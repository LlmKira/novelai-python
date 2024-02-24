# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 上午11:29
# @Author  : sudoskys
# @File    : upscale.py
# @Software: PyCharm
from typing import Tuple

from pydantic import BaseModel

from ..schema import RespBase


class UpscaleResp(RespBase):
    class RequestParams(BaseModel):
        endpoint: str
        raw_request: dict = None

    meta: RequestParams
    files: Tuple[str, bytes] = None
