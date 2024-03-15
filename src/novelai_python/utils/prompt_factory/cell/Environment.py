# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Environment = ['中型陆地哺乳', '主题', '交通', '交通工具', '人造景观', '其他', '军事', '办公', '园林', '场地',
                '大型陆地哺乳', '太空', '娱乐旅宿', '室内其他', '室外其他', '家居', '小型陆地哺乳', '屋外', '工业',
                '市政', '市镇', '幻兽种', '建筑', '建筑风格', '恐龙', '果实', '树木', '校园', '水产', '海洋哺乳',
                '游乐设施', '灌木', '爬行两栖', '自然景观', '自然环境', '节肢', '花', '草', '藤类', '设施', '购物',
                '运动场', '餐饮', '鸟类']


@dataclass(frozen=True, order=True)
class EnvironmentType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Environment.json')
        return data

    MEDIUM_TERRESTRIAL_MAMMAL = '中型陆地哺乳'
    THEME = '主题'
    TRANSPORTATION = '交通'
    VEHICLE = '交通工具'
    MAN_MADE_SCENERY = '人造景观'
    OTHER = '其他'
    MILITARY = '军事'
    OFFICE = '办公'
    GARDEN = '园林'
    SITE = '场地'
    LARGE_TERRESTRIAL_MAMMAL = '大型陆地哺乳'
    SPACE = '太空'
    ENTERTAINMENT_ACCOMMODATION = '娱乐旅宿'
    INDOOR_OTHER = '室内其他'
    OUTDOOR_OTHER = '室外其他'
    HOME = '家居'
    SMALL_TERRESTRIAL_MAMMAL = '小型陆地哺乳'
    OUTDOOR = '屋外'
    INDUSTRY = '工业'
    MUNICIPAL = '市政'
    TOWN = '市镇'
    MAGICAL_BEAST_SPECIES = '幻兽种'
    ARCHITECTURE = '建筑'
    ARCHITECTURAL_STYLE = '建筑风格'
    DINOSAUR = '恐龙'
    FRUIT = '果实'
    TREE = '树木'
    CAMPUS = '校园'
    AQUATIC = '水产'
    MARINE_MAMMAL = '海洋哺乳'
    AMUSEMENT_FACILITIES = '游乐设施'
    SHRUB = '灌木'
    REPTILIAN_AMPHIBIAN = '爬行两栖'
    NATURAL_LANDSCAPE = '自然景观'
    NATURAL_ENVIRONMENT = '自然环境'
    ARTHROPOD = '节肢'
    FLOWER = '花'
    GRASS = '草'
    VINE = '藤类'
    FACILITY = '设施'
    SHOPPING = '购物'
    SPORTS_FIELD = '运动场'
    CATERING = '餐饮'
    BIRD = '鸟类'
