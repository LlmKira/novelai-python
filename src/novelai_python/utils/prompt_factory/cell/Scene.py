# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Scene = ['一天', '光', '其他画面', '其他符号', '功能', '动画', '四季', '封面和书本', '影', '插画和CG', '气泡', '滤镜',
          '漫画', '画面元素', '画面增强', '线条', '节日', '设定', '音符', '颜色风格']


@dataclass(frozen=True, order=True)
class SceneType(BaseCell):
    def source(self):
        data = pathlib.Path(__file__).parent.joinpath('raw/Scene.json')
        return data

    DAYTIME = '一天'
    LIGHT = '光'
    OTHER_SCENES = '其他画面'
    OTHER_SYMBOLS = '其他符号'
    FUNCTION = '功能'
    ANIMATION = '动画'
    SEASONS = '四季'
    COVERS_AND_BOOKS = '封面和书本'
    SHADOW = '影'
    ILLUSTRATIONS_AND_CG = '插画和CG'
    BUBBLE = '气泡'
    FILTER = '滤镜'
    COMICS = '漫画'
    SCENE_ELEMENTS = '画面元素'
    SCENE_ENHANCEMENT = '画面增强'
    LINE = '线条'
    HOLIDAY = '节日'
    SETTINGS = '设定'
    MUSIC_NOTES = '音符'
    COLOR_STYLE = '颜色风格'
