# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Face = ['修饰', '其他', '嘴巴', '整体', '眉毛', '眼部', '眼部装饰', '瞳孔形状', '颜色', '额头']


@dataclass(frozen=True, order=True)
class FaceType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Face.json')
        return data

    EMBELLISHMENT = '修饰'
    OTHER = '其他'
    MOUTH = '嘴巴'
    OVERALL = '整体'
    EYEBROWS = '眉毛'
    EYE_REGION = '眼部'
    EYE_DECORATION = '眼部装饰'
    PUPIL_SHAPE = '瞳孔形状'
    COLOR = '颜色'
    FOREHEAD = '额头'
