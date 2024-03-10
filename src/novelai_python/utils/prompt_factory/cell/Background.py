# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Background = ['乐器', '图案背景', '实物背景', '室外设施', '家具', '工具', '幻想系', '摆设', '电器', '简单色背景',
               '自然物', '装修', '载具']


@dataclass(frozen=True, order=True)
class BackgroundType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Background.json')
        return data

    INSTRUMENT = '乐器'
    PATTERN_BACKGROUND = '图案背景'
    PHYSICAL_BACKGROUND = '实物背景'
    OUTDOOR_FACILITY = '室外设施'
    FURNITURE = '家具'
    TOOLS = '工具'
    FANTASY = '幻想系'
    DECORATIONS = '摆设'
    APPLIANCE = '电器'
    SIMPLE_COLOR_BACKGROUND = '简单色背景'
    NATURE = '自然物'
    DECORATION = '装修'
    VEHICLE = '载具'
