# -*- coding: utf-8 -*-
from enum import Enum

_Accessories = ['主题发饰', '乐器', '体育', '其他', '其他1', '其他2', '其他3', '厨具', '头顶', '容器', '尾巴', '工具',
                '手套', '数码', '文具', '日用', '材料', '武器', '汤和饮料', '玩具', '甜点', '翅膀', '耳饰', '肉禽蛋',
                '胸部', '脸部', '腕臂', '腰部', '腿脚', '调味料和酱汁', '颈饰', '食物', '餐具', '鱼和海鲜']


class AccessoryType(Enum):
    THEME_DECORATIONS = '主题发饰'
    INSTRUMENTS = '乐器'
    SPORTS = '体育'
    OTHER1 = '其他'
    OTHER2 = '其他1'
    OTHER3 = '其他2'
    OTHER4 = '其他3'
    KITCHENWARE = '厨具'
    HEAD = '头顶'
    CONTAINER = '容器'
    TAIL = '尾巴'
    TOOLS = '工具'
    GLOVES = '手套'
    DIGITAL = '数码'
    STATIONERY = '文具'
    DAILY_USE = '日用'
    MATERIALS = '材料'
    WEAPONS = '武器'
    SOUP_AND_DRINKS = '汤和饮料'
    TOYS = '玩具'
    DESSERTS = '甜点'
    WINGS = '翅膀'
    EAR_DECORATIONS = '耳饰'
    MEAT_POULTRY_AND_EGGS = '肉禽蛋'
    CHEST = '胸部'
    FACE = '脸部'
    ARM_WRIST = '腕臂'
    WAIST = '腰部'
    LEG_FOOT = '腿脚'
    CONDIMENTS_AND_SAUCE = '调味料和酱汁'
    NECK_DECORATIONS = '颈饰'
    FOOD = '食物'
    TABLEWARE = '餐具'
    FISH_AND_SEAFOOD = '鱼和海鲜'
