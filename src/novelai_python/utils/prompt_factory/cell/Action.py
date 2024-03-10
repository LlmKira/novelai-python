# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Action = ['互动', '体育运动', '倒立', '倾靠', '其他1', '其他互动', '其他姿势', '双人姿势', '坐姿', '头发互动',
           '头部姿势', '娱乐', '室内日常', '战斗', '户外', '手位置', '手指姿势', '手臂姿势', '指向', '数码', '文具',
           '日用', '桌案', '植物', '武器', '沐浴', '活动', '玩具', '移动', '穿脱衣', '站姿', '胸部姿势', '腿部姿势',
           '艺术', '衣服互动', '趴姿', '跪姿', '躺姿', '造型', '音乐', '食物', '魔幻']


@dataclass(frozen=True, order=True)
class ActionType(BaseCell):
    def source(self):
        # 获取当前文件夹下的raw文件夹中的json文件
        data = pathlib.Path(__file__).parent.joinpath('raw/Action.json')
        return data

    INTERACTION = '互动'
    SPORT = '体育运动'
    HANDSTAND = '倒立'
    LEANING = '倾靠'
    OTHER1 = '其他1'
    OTHER_INTERACTION = '其他互动'
    OTHER_POSTURE = '其他姿势'
    DOUBLE_POSTURE = '双人姿势'
    SITTING = '坐姿'
    HAIR_INTERACTION = '头发互动'
    HEAD_POSTURE = '头部姿势'
    ENTERTAINMENT = '娱乐'
    INDOOR_DAILY = '室内日常'
    BATTLE = '战斗'
    OUTDOOR = '户外'
    HAND_POSITION = '手位置'
    FINGER_POSTURE = '手指姿势'
    ARM_POSTURE = '手臂姿势'
    POINTING = '指向'
    DIGITAL = '数码'
    STATIONERY = '文具'
    DAILY_USE = '日用'
    DESK_CASE = '桌案'
    PLANT = '植物'
    WEAPON = '武器'
    BATHING = '沐浴'
    ACTIVITY = '活动'
    TOY = '玩具'
    MOVEMENT = '移动'
    DRESSING = '穿脱衣'
    STANDING = '站姿'
    BREAST_POSTURE = '胸部姿势'
    LEG_POSTURE = '腿部姿势'
    ART = '艺术'
    CLOTHES_INTERACTION = '衣服互动'
    PRONE_POSTURE = '趴姿'
    KNEELING = '跪姿'
    LYING = '躺姿'
    STYLING = '造型'
    MUSIC = '音乐'
    FOOD = '食物'
    MAGIC = '魔幻'
