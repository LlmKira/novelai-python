# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Art_style = ['传统材质', '作品', '其他风格', '年代风', '流派', '艺术家']


@dataclass(frozen=True, order=True)
class Art_StyleType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Art_Style.json')
        return data

    TRADITIONAL_MATERIALS = '传统材质'
    ARTWORK = '作品'
    OTHER_STYLES = '其他风格'
    ERA_STYLE = '年代风'
    GENRE = '流派'
    ARTIST = '艺术家'
