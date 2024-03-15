# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Expression = ['其他', '哀', '喜', '嘴', '怒', '惊', '慌', '眼', '累', '羞']


@dataclass(frozen=True, order=True)
class ExpressionType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Expression.json')
        return data

    OTHER = '其他'
    SADNESS = '哀'
    JOY = '喜'
    MOUTH = '嘴'
    ANGER = '怒'
    SURPRISE = '惊'
    PANIC = '慌'
    EYE = '眼'
    TIRED = '累'
    SHY = '羞'
