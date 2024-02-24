# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午11:16
# @Author  : sudoskys
# @File    : text2image.py
# @Software: PyCharm
from typing import Tuple, List

from pydantic import BaseModel

from ..schema import RespBase


class ImageGenerateResp(RespBase):
    class RequestParams(BaseModel):
        endpoint: str
        raw_request: dict = None

    meta: RequestParams
    files: List[Tuple[str, bytes]] = None

    def query_params(self, key: str, default=None):
        if not isinstance(self.meta.raw_request.get("parameters"), dict):
            raise Exception("Resp parameters is not dict")
        return self.meta.raw_request.get("parameters").get(key, default)


class SuggestTagsResp(RespBase):
    class Tag(BaseModel):
        tag: str
        count: int
        confidence: float

    tags: List[Tag] = None
