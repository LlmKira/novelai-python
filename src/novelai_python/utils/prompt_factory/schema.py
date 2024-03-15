# -*- coding: utf-8 -*-
# @Time    : 2024/2/10 下午2:13
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import random

from pydantic import BaseModel, Field, ConfigDict


class CellContent(BaseModel):
    """
    单元
    """
    title: str = Field("", title="标题")
    tags: list = Field([], title="标签")

    model_config = ConfigDict()

    def random_tags(self):
        """
        随机标签
        :return:
        """
        return random.choice(self.tags)


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton
