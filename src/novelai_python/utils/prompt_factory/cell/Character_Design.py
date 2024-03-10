# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass

from .cell_schema import BaseCell

_Character_design = ['人外', '人物关系', '其他', '年龄', '幻想系职业', '性格', '机设', '现实系职业', '皮肤', '组成',
                     '非人']


@dataclass(frozen=True, order=True)
class Character_DesignType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Character_Design.json')
        return data

    NON_HUMAN = '人外'
    CHARACTER_RELATIONSHIP = '人物关系'
    OTHER = '其他'
    AGE = '年龄'
    FANTASY_JOB = '幻想系职业'
    PERSONALITY = '性格'
    MACHINERY = '机设'
    REALISTIC_JOB = '现实系职业'
    SKIN = '皮肤'
    COMPOSITION = '组成'
    NON_HUMAN_SPECIES = '非人'
