# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Clothing = ['上衣', '下装', '中古系', '仪式', '兜帽', '其他', '其他种类', '内衣', '内衬', '内裤', '制服', '卫衣',
             '吊带', '和服', '大衣', '头部', '夹克', '居家', '开口', '情趣', '扣式',
             '披风兜帽', '整体', '服装纹样', '未来系', '比基尼', '毛衣', '汉服', '泳衣', '洛丽塔', '现代系', '种族cos',
             '紧身衣', '职业cos', '背心', '节日', '衬衫', '袖子', '袜子', '装饰', '裙子', '裤子', '运动系', '连衣裙',
             '雨衣', '非衣服当衣服', '鞋子', '领子']


@dataclass(frozen=True, order=True)
class ClothingType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Clothing.json')
        return data

    TOP = '上衣'
    BOTTOM = '下装'
    MEDIEVAL = '中古系'
    CEREMONIAL = '仪式'
    HOOD = '兜帽'
    OTHER = '其他'
    OTHER_TYPES = '其他种类'
    UNDERWEAR = '内衣'
    LINING = '内衬'
    PANTIES = '内裤'
    UNIFORM = '制服'
    HOODIE = '卫衣'
    SUSPENDERS = '吊带'
    KIMONO = '和服'
    COAT = '大衣'
    HEAD = '头部'
    JACKET = '夹克'
    HOME_CLOTHES = '居家'
    OPEN_CLOTHING = '开口'
    SEXY = '情趣'
    BUTTON_CLOTHING = '扣式'
    CAPED_HOOD = '披风兜帽'
    OVERALL = '整体'
    CLOTHING_PATTERN = '服装纹样'
    FUTURE = '未来系'
    BIKINI = '比基尼'
    SWEATER = '毛衣'
    HAN_CLOTHING = '汉服'
    SWIMSUIT = '泳衣'
    LOLITA = '洛丽塔'
    MODERN = '现代系'
    RACE_COSPLAY = '种族cos'
    TIGHT_FITTING = '紧身衣'
    JOB_COSPLAY = '职业cos'
    VEST = '背心'
    HOLIDAY = '节日'
    SHIRT = '衬衫'
    SLEEVE = '袖子'
    SOCK = '袜子'
    DECORATION = '装饰'
    SKIRT = '裙子'
    PANTS = '裤子'
    SPORTS = '运动系'
    DRESS = '连衣裙'
    RAINCOAT = '雨衣'
    NON_CLOTHING_AS_CLOTHING = '非衣服当衣服'
    SHOES = '鞋子'
    COLLAR = '领子'
