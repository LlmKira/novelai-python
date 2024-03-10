# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Composition = ['主题', '人物视线', '其他', '区域', '叶', '地平线', '天空', '日月', '昆虫', '构成', '火焰和爆炸', '烟',
                '焦点', '纸', '背景关系', '自然现象', '花', '视角', '角度', '设计元素', '远近', '透视', '魔幻']


@dataclass(frozen=True, order=True)
class CompositionType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Composition.json')
        return data

    THEME = '主题'
    CHARACTER_SIGHTLINE = '人物视线'
    OTHER = '其他'
    REGION = '区域'
    LEAF = '叶'
    HORIZON = '地平线'
    SKY = '天空'
    SUN_MOON = '日月'
    INSECT = '昆虫'
    COMPOSITION = '构成'
    FIRE_AND_EXPLOSION = '火焰和爆炸'
    SMOKE = '烟'
    FOCUS = '焦点'
    PAPER = '纸'
    BACKGROUND_RELATIONSHIP = '背景关系'
    NATURAL_PHENOMENON = '自然现象'
    FLOWER = '花'
    PERSPECTIVE = '视角'
    ANGLE = '角度'
    DESIGN_ELEMENT = '设计元素'
    DISTANCE = '远近'
    PERSPECTIVE_VISION = '透视'
    FANTASY = '魔幻'
