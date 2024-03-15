# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Body = ['侧发', '其他', '其他装饰', '兽耳', '刘海', '发质', '发量', '发髻', '手', '整体发型', '特殊耳', '肩', '胸',
         '腰部', '腹部', '腿部', '臀部', '花纹', '角', '足部', '辫子', '长度', '颈背', '颜色', '马尾']


@dataclass(frozen=True, order=True)
class BodyType(BaseCell):
    def source(self):
        data = pathlib.Path(__file__).parent.joinpath('raw/Body.json')
        return data

    SIDE_HAIR = '侧发'
    OTHER = '其他'
    OTHER_DECORATIONS = '其他装饰'
    ANIMAL_EARS = '兽耳'
    BANGS = '刘海'
    HAIR_QUALITY = '发质'
    HAIR_VOLUME = '发量'
    HAIR_BUN = '发髻'
    HAND = '手'
    OVERALL_HAIRSTYLE = '整体发型'
    SPECIAL_EARS = '特殊耳'
    SHOULDER = '肩'
    CHEST = '胸'
    WAIST = '腰部'
    ABDOMEN = '腹部'
    LEG = '腿部'
    HIP = '臀部'
    PATTERN = '花纹'
    HORN = '角'
    FOOT = '足部'
    BRAID = '辫子'
    LENGTH = '长度'
    NECK_BACK = '颈背'
    COLOR = '颜色'
    PONYTAIL = '马尾'
