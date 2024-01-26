# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午1:10
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import Tuple

from pydantic import BaseModel


class NaiResult(BaseModel):
    class RequestParams(BaseModel):
        endpoint: str
        raw_request: dict = None

    meta: RequestParams
    files: Tuple[str, bytes] = None

    def query_params(self, key: str, default=None):
        if isinstance(self.meta.raw_request, str):
            return default
        if isinstance(self.meta.raw_request.get("parameters"), dict):
            return self.meta.raw_request.get("parameters").get(key, default)
        return default
