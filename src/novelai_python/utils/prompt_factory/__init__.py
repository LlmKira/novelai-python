# -*- coding: utf-8 -*-
# @Time    : 2024/2/10 下午1:50
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import json
import pathlib
import random
from dataclasses import dataclass
from typing import Type, List

from pydantic import BaseModel, field_validator, ConfigDict

from .cell import Accessories
from .cell import Action
from .cell import Art_Style
from .cell import Background
from .cell import Body
from .cell import Character_Design
from .cell import Clothing
from .cell import Composition
from .cell import Environment
from .cell import Expression
from .cell import Face
from .cell import Illustrator
from .cell import Scene
from .cell import r18
from .cell.cell_schema import BaseCell
from .schema import singleton

data_dir = pathlib.Path(__file__).parent.joinpath('cell/raw')
if not data_dir.exists():
    raise FileNotFoundError("Prompt Factory Data directory not found.")
_data_map = {}


@dataclass(frozen=True, order=True)
class DataSelector(object):
    """
    选择器
    """
    R18 = r18.R18Type()
    """R18"""
    ILLUSTRATOR = Illustrator.IllustratorType()
    """画师"""
    CHARACTER_DESIGN = Character_Design.Character_DesignType()
    """角色设计"""
    ACCESSORIES = Accessories.AccessoryType()
    """配饰"""
    CLOTHING = Clothing.ClothingType()
    """服装"""
    BODY = Body.BodyType()
    """身体"""
    FACE = Face.FaceType()
    """脸"""
    EXPRESSION = Expression.ExpressionType()
    """表情"""
    BACKGROUND = Background.BackgroundType()
    """背景"""
    ART_STYLE = Art_Style.Art_StyleType()
    """艺术风格"""
    SCENE = Scene.SceneType()
    """场景"""
    ENVIRONMENT = Environment.EnvironmentType()
    """环境"""
    ACTION = Action.ActionType()
    """动作"""
    COMPOSITION = Composition.CompositionType()
    """构图"""


class Loader(BaseModel):
    source: BaseCell
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def attributes(self):
        return self.source.get_values()

    @property
    def data(self):

        if _data_map.get(self.source.source(), None) is None:
            with open(data_dir.joinpath(self.source.source()), "r", encoding="utf-8") as f:
                _data_map[self.source.source()] = json.load(f)
        return _data_map[self.source.source()]

    @field_validator("source")
    def check_file_exist(cls, v: BaseCell):
        """
        检查文件是否存在
        :param v:
        :return:
        """
        if not data_dir.joinpath(v.source()).exists():
            raise FileNotFoundError(f"Prompt Factory Data file not found: {v.source()}")
        return v

    @staticmethod
    def refine_tag(tag: str):
        """
        如果存在 // 则取前面的，并 strip
        :param tag:
        :return:
        """
        if "//" in tag:
            return tag.split("//")[0].strip()
        return tag.strip()

    def random_tag(self, sub_type: str, n: int = 1):
        """
        随机选择 n 个标签
        :param sub_type: 子类型
        :param n: 选择的数量
        :return:
        """
        _sub_data = self.data.get(sub_type, None)
        if _sub_data is None:
            raise KeyError(f"Sub type {sub_type} not found in {self.source}")
        assert isinstance(_sub_data, dict), f"Sub type {sub_type} not a dict"
        if n > len(_sub_data.keys()):
            n = len(_sub_data.keys())
        random_key = random.sample(list(_sub_data.keys()), n)
        _pair = []
        for k in random_key:
            _pair.append((_sub_data[k], self.refine_tag(k)))
        return _pair


class Generator(BaseModel):
    """
    生成器
    """
    pool: List[BaseCell]
    class_sample: int = 1
    """类型选择数"""
    class_piece: int = 1
    """浮动量"""
    tag_sample: int = 1
    """标签选择数"""
    tag_piece: int = 3
    """浮动量"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    def build_loader(source: BaseCell):
        return Loader(source=source)

    def generate_pool(self):
        """
        遍历 Pool 中的类型，然后随机选择大类，然后随机选择标签，最后返回元组
        :return:
        """
        _tag = []
        for crs in self.pool:
            _loader = self.build_loader(crs)
            # 从类型中随机选择大类
            class_sample_num = self.class_sample + random.randint(-self.class_piece, self.class_piece)
            class_sample_num = 1 if class_sample_num < 1 else class_sample_num
            class_sample_num = len(_loader.attributes) if class_sample_num > len(
                _loader.attributes) else class_sample_num
            _class = random.sample(_loader.attributes, class_sample_num)
            for c in _class:
                tag_sample_num = self.tag_sample + random.randint(-self.tag_piece, self.tag_piece)
                tag_sample_num = 1 if tag_sample_num < 1 else tag_sample_num
                _tags = _loader.random_tag(sub_type=c, n=tag_sample_num)
                _tag.extend(_tags)
        return _tag

    @staticmethod
    def random_tag(top_type: BaseCell, sub_type: str, n: int = 1):
        """
        随机选择 n 个标签
        :param top_type: 类型
        :param sub_type: 子类型
        :param n: 选择的数量
        :return:
        """
        _loader = Loader(source=top_type)
        return _loader.random_tag(sub_type=sub_type, n=n)

    @staticmethod
    def random_weighted(choices: List[tuple], return_list: bool = True):
        """
        随机加权选择
        :param choices: 选择
        :param return_list: 是否返回列表
        :return:
        """
        # 提取值与权重
        values, weights = zip(*choices)
        # 根据权重随机选择
        random_choice = random.choices(values, weights)
        if return_list:
            return random_choice
        else:
            return random_choice[0]

    @staticmethod
    def check_list_empty(types: List):
        """
        检查列表是否含有 Str
        :param types:
        :return:
        """
        _all_none = True
        for t in types:
            if t is not None:
                _all_none = False
                break
        return _all_none

    @staticmethod
    def enhance_tag(tag: str, n: int = 0):
        """
        增强标签，给标签加上 {}
        :param n:  加强度
        :param tag:  标签
        :return:
        """
        return "{" * n + tag + "}" * n

    def generate(self,
                 enable_nsfw: bool = False,
                 enable_illustrator: bool = False,
                 ):
        """
        生成
        :param enable_nsfw: 是否启用 r18
        :param enable_illustrator: 是否启用画师
        :return:
        """
        _tag = []
        # 条件组
        gender = self.random_weighted([("boy", 20), ("girl", 80)], return_list=False)
        num_of_characters = self.random_weighted([(1, 60), (2, 30), (3, 10)], return_list=False)
        # 视线
        COMPOSITION_IF = []
        THEME_AND_AREA = [
            (DataSelector.COMPOSITION.THEME, 20),
            (DataSelector.COMPOSITION.REGION, 20),
            (DataSelector.COMPOSITION.ANGLE, 20),
            (DataSelector.COMPOSITION.DISTANCE, 20),
            (None, 120)
        ]
        SIGHTLINE_AND_FOCUS = [
            (DataSelector.COMPOSITION.CHARACTER_SIGHTLINE, 20),
            (DataSelector.COMPOSITION.FOCUS, 20),
            (DataSelector.COMPOSITION.PERSPECTIVE, 20),
            (DataSelector.COMPOSITION.PERSPECTIVE_VISION, 20),
            (DataSelector.COMPOSITION.BACKGROUND_RELATIONSHIP, 20),
            (None, 120)
        ]
        NATURAL_ELEMENTS = [
            (DataSelector.COMPOSITION.LEAF, 15),
            (DataSelector.COMPOSITION.SKY, 15),
            (DataSelector.COMPOSITION.SUN_MOON, 15),
            (DataSelector.COMPOSITION.FIRE_AND_EXPLOSION, 15),
            (DataSelector.COMPOSITION.SMOKE, 15),
            (DataSelector.COMPOSITION.NATURAL_PHENOMENON, 15),
            (DataSelector.COMPOSITION.FLOWER, 15),
            (None, 95)
        ]
        DESIGN_ELEMENTS = [
            (DataSelector.COMPOSITION.DESIGN_ELEMENT, 30),
            (DataSelector.COMPOSITION.COMPOSITION, 30),
            (DataSelector.COMPOSITION.FANTASY, 30),
            (None, 110)
        ]
        OTHER_ELEMENTS = [
            (DataSelector.COMPOSITION.OTHER, 30),
            (DataSelector.COMPOSITION.INSECT, 30),
            (DataSelector.COMPOSITION.PAPER, 30),
            (None, 110)
        ]
        COMPOSITION_IF.extend(
            self.random_weighted(
                THEME_AND_AREA
            )
        )
        COMPOSITION_IF.extend(
            self.random_weighted(
                SIGHTLINE_AND_FOCUS
            )
        )
        if self.check_list_empty(COMPOSITION_IF):
            if random.random() > 0.5:
                COMPOSITION_IF.extend(
                    self.random_weighted(
                        NATURAL_ELEMENTS
                    )
                )
            else:
                COMPOSITION_IF.extend(
                    self.random_weighted(
                        DESIGN_ELEMENTS
                    )
                )
            COMPOSITION_IF.extend(
                self.random_weighted(
                    OTHER_ELEMENTS
                )
            )
        SCENE_IF = []
        TIME_AND_ENVIRONMENT = [
            (DataSelector.SCENE.DAYTIME, 25),
            (DataSelector.SCENE.SEASONS, 25),
            (DataSelector.SCENE.OTHER_SCENES, 25),
            (None, 125)
        ]
        VISUAL_RENDERING = [
            (DataSelector.SCENE.LIGHT, 25),
            (DataSelector.SCENE.SHADOW, 25),
            (DataSelector.SCENE.COLOR_STYLE, 25),
            (DataSelector.SCENE.FILTER, 25),
            (None, 100)
        ]
        SCENE_DECORATIONS = [
            (DataSelector.SCENE.SCENE_ELEMENTS, 20),
            (DataSelector.SCENE.SCENE_ENHANCEMENT, 20),
            (DataSelector.SCENE.LINE, 20),
            (DataSelector.SCENE.BUBBLE, 20),
            (DataSelector.SCENE.MUSIC_NOTES, 20),
            (None, 100)
        ]
        SPECIAL_CATEGORIES = [
            (DataSelector.SCENE.ILLUSTRATIONS_AND_CG, 20),
            (DataSelector.SCENE.ANIMATION, 20),
            (DataSelector.SCENE.HOLIDAY, 20),
            (DataSelector.SCENE.COVERS_AND_BOOKS, 20),
            (DataSelector.SCENE.COMICS, 20),
            (None, 100)
        ]
        OTHER = [
            (DataSelector.SCENE.OTHER_SYMBOLS, 30),
            (DataSelector.SCENE.FUNCTION, 30),
            (DataSelector.SCENE.SETTINGS, 30),
            (None, 110)
        ]
        SCENE_IF.extend(
            self.random_weighted(
                SPECIAL_CATEGORIES
            )
        )
        if self.check_list_empty(SCENE_IF):
            SCENE_IF.extend(
                self.random_weighted(
                    TIME_AND_ENVIRONMENT
                )
            )
        SCENE_IF.extend(
            self.random_weighted(
                VISUAL_RENDERING
            )
        )
        if random.random() > 0.5:
            SCENE_IF.extend(
                self.random_weighted(
                    SCENE_DECORATIONS
                )
            )
        if random.random() > 0.5:
            SCENE_IF.extend(
                self.random_weighted(
                    OTHER
                )
            )
        ENVIRONMENT_IF = []
        BUILDINGS_AND_FACILITIES = [
            (DataSelector.ENVIRONMENT.ARCHITECTURE, 20),
            (DataSelector.ENVIRONMENT.ARCHITECTURAL_STYLE, 20),
            (DataSelector.ENVIRONMENT.OFFICE, 20),
            (DataSelector.ENVIRONMENT.HOME, 20),
            (DataSelector.ENVIRONMENT.ENTERTAINMENT_ACCOMMODATION, 20),
            (DataSelector.ENVIRONMENT.SHOPPING, 20),
            (DataSelector.ENVIRONMENT.CATERING, 20),
            (DataSelector.ENVIRONMENT.FACILITY, 20),
            (DataSelector.ENVIRONMENT.MUNICIPAL, 20),
            (DataSelector.ENVIRONMENT.INDUSTRY, 20),
            (DataSelector.ENVIRONMENT.MILITARY, 20),
            (DataSelector.ENVIRONMENT.CAMPUS, 20),
            (DataSelector.ENVIRONMENT.SPORTS_FIELD, 20),
            (DataSelector.ENVIRONMENT.AMUSEMENT_FACILITIES, 20),
            (None, 700)
        ]
        NATURAL_ENVIRONMENT = [
            (DataSelector.ENVIRONMENT.NATURAL_LANDSCAPE, 25),
            (DataSelector.ENVIRONMENT.NATURAL_ENVIRONMENT, 25),
            (DataSelector.ENVIRONMENT.TREE, 25),
            (DataSelector.ENVIRONMENT.FLOWER, 25),
            (DataSelector.ENVIRONMENT.GRASS, 25),
            (DataSelector.ENVIRONMENT.SHRUB, 25),
            (DataSelector.ENVIRONMENT.FRUIT, 25),
            (DataSelector.ENVIRONMENT.VINE, 25),
            (None, 300)
        ]
        ANIMAL_ELEMENTS = [
            (DataSelector.ENVIRONMENT.SMALL_TERRESTRIAL_MAMMAL, 15),
            (DataSelector.ENVIRONMENT.MEDIUM_TERRESTRIAL_MAMMAL, 15),
            (DataSelector.ENVIRONMENT.LARGE_TERRESTRIAL_MAMMAL, 15),
            (DataSelector.ENVIRONMENT.AQUATIC, 15),
            (DataSelector.ENVIRONMENT.MARINE_MAMMAL, 15),
            (DataSelector.ENVIRONMENT.ARTHROPOD, 15),
            (DataSelector.ENVIRONMENT.BIRD, 15),
            (DataSelector.ENVIRONMENT.REPTILIAN_AMPHIBIAN, 15),
            (DataSelector.ENVIRONMENT.DINOSAUR, 15),
            (DataSelector.ENVIRONMENT.MAGICAL_BEAST_SPECIES, 15),
            (None, 400)
        ]
        TRANSPORTATION = [
            (DataSelector.ENVIRONMENT.TRANSPORTATION, 50),
            (DataSelector.ENVIRONMENT.VEHICLE, 50),
            (None, 200)
        ]
        OTHER = [
            (DataSelector.ENVIRONMENT.OTHER, 20),
            (DataSelector.ENVIRONMENT.THEME, 20),
            (DataSelector.ENVIRONMENT.SITE, 20),
            (DataSelector.ENVIRONMENT.OUTDOOR, 20),
            (DataSelector.ENVIRONMENT.INDOOR_OTHER, 20),
            (DataSelector.ENVIRONMENT.OUTDOOR_OTHER, 20),
            (None, 200)
        ]

        ENVIRONMENT_IF.extend(
            self.random_weighted(
                BUILDINGS_AND_FACILITIES
            )
        )
        if self.check_list_empty(ENVIRONMENT_IF):
            ENVIRONMENT_IF.extend(
                self.random_weighted(
                    NATURAL_ENVIRONMENT
                )
            )
            ENVIRONMENT_IF.extend(
                self.random_weighted(
                    ANIMAL_ELEMENTS
                )
            )
        else:
            ENVIRONMENT_IF.extend(
                self.random_weighted(
                    TRANSPORTATION
                )
            )
        ENVIRONMENT_IF.extend(
            self.random_weighted(
                OTHER
            )
        )
        BACKGROUND_IF = []
        BACKGROUND_IF.extend(
            self.random_weighted(
                [
                    (DataSelector.BACKGROUND.PHYSICAL_BACKGROUND, 15),
                    (DataSelector.BACKGROUND.PATTERN_BACKGROUND, 20),
                    (DataSelector.BACKGROUND.SIMPLE_COLOR_BACKGROUND, 50),
                    (None, 80),
                ]
            )
        )
        if self.check_list_empty(BACKGROUND_IF):
            BACKGROUND_IF.extend(
                self.random_weighted(
                    [
                        (DataSelector.BACKGROUND.NATURE, 25),
                        (DataSelector.BACKGROUND.FANTASY, 15),
                        (DataSelector.BACKGROUND.INSTRUMENT, 15),
                        (DataSelector.BACKGROUND.OUTDOOR_FACILITY, 10),
                        (DataSelector.BACKGROUND.FURNITURE, 10),
                        (DataSelector.BACKGROUND.TOOLS, 5),
                        (DataSelector.BACKGROUND.DECORATIONS, 30),
                        (DataSelector.BACKGROUND.APPLIANCE, 12),
                        (DataSelector.BACKGROUND.VEHICLE, 20),
                        (None, 100),
                    ]
                )
            )
        R18_IF = []
        if enable_nsfw:
            R18_IF.extend(
                self.random_weighted(
                    [
                        (DataSelector.R18.TAG_17_9, 100),
                    ]
                )
            )
            R18_IF.extend(
                self.random_weighted(
                    [
                        (DataSelector.R18.TAG_17_9, 100),
                    ]
                )
            )
        ACTION_IF = []
        BODY_POSTURES = [
            (DataSelector.ACTION.HANDSTAND, 15),
            (DataSelector.ACTION.LEANING, 15),
            (DataSelector.ACTION.SITTING, 15),
            (DataSelector.ACTION.STANDING, 15),
            (DataSelector.ACTION.HEAD_POSTURE, 15),
            (DataSelector.ACTION.HAND_POSITION, 15),
            (DataSelector.ACTION.FINGER_POSTURE, 15),
            (DataSelector.ACTION.ARM_POSTURE, 15),
            (DataSelector.ACTION.BREAST_POSTURE, 15),
            (DataSelector.ACTION.LEG_POSTURE, 15),
            (DataSelector.ACTION.PRONE_POSTURE, 15),
            (DataSelector.ACTION.KNEELING, 15),
            (DataSelector.ACTION.LYING, 15),
            (None, 115)
        ]
        ACTIVITIES_AND_SPORTS = [
            (DataSelector.ACTION.ENTERTAINMENT, 25),
            (DataSelector.ACTION.SPORT, 25),
            (DataSelector.ACTION.BATTLE, 25),
            (DataSelector.ACTION.DAILY_USE, 25),
            (DataSelector.ACTION.MOVEMENT, 25),
            (None, 175)
        ]
        DAILY_ACCESSORIES = [
            (DataSelector.ACTION.DIGITAL, 30),
            (DataSelector.ACTION.STATIONERY, 30),
            (DataSelector.ACTION.DAILY_USE, 30),
            (DataSelector.ACTION.DESK_CASE, 30),
            (DataSelector.ACTION.TOY, 30),
            (None, 150)
        ]
        CLOTHING_AND_HAIRSTYLE = [
            (DataSelector.ACTION.CLOTHES_INTERACTION, 50),
            (DataSelector.ACTION.HAIR_INTERACTION, 50),
            (DataSelector.ACTION.DRESSING, 50),
            (None, 150)
        ]
        SPECIAL_CATEGORIES = [
            (DataSelector.ACTION.OTHER_INTERACTION, 20),
            (DataSelector.ACTION.BATTLE, 20),
            (DataSelector.ACTION.MAGIC, 20),
            (DataSelector.ACTION.MUSIC, 20),
            (DataSelector.ACTION.FOOD, 20),
            (None, 500)
        ]
        OTHER = [
            (DataSelector.ACTION.OTHER_POSTURE, 50),
            (DataSelector.ACTION.OTHER1, 50),
            (None, 200)
        ]
        ACTION_IF.extend(
            self.random_weighted(
                SPECIAL_CATEGORIES
            )
        )
        if self.check_list_empty(ACTION_IF):
            ACTION_IF.extend(
                self.random_weighted(
                    ACTIVITIES_AND_SPORTS
                )
            )
        if self.check_list_empty(ACTION_IF):
            ACTION_IF.extend(
                self.random_weighted(
                    DAILY_ACCESSORIES
                )
            )
        ACTION_IF.extend(
            self.random_weighted(
                CLOTHING_AND_HAIRSTYLE
            )
        )
        ACTION_IF.extend(
            self.random_weighted(
                OTHER
            )
        )
        if num_of_characters > 1:
            ACTION_IF.extend(
                self.random_weighted(
                    [
                        (DataSelector.ACTION.DOUBLE_POSTURE, 10),
                        (None, 15),
                    ]
                )
            )
        else:
            ACTION_IF.extend(
                self.random_weighted(
                    BODY_POSTURES
                )
            )
        ART_STYLE_IF = []
        ART_STYLE_IF.extend(
            self.random_weighted(
                [
                    (DataSelector.ART_STYLE.TRADITIONAL_MATERIALS, 20),
                    (DataSelector.ART_STYLE.ARTWORK, 5),
                    (DataSelector.ART_STYLE.OTHER_STYLES, 15),
                    (DataSelector.ART_STYLE.ERA_STYLE, 3),
                    (DataSelector.ART_STYLE.GENRE, 10),
                    (DataSelector.ART_STYLE.ARTIST, 3),
                    (None, 200),
                ]
            )
        )
        ILLUSTRATOR_IF = []
        if enable_illustrator:
            ILLUSTRATOR_IF.extend(
                self.random_weighted(
                    [
                        (DataSelector.ILLUSTRATOR.PAINTER, 100),
                    ]
                )
            )
        CHARACTER_DESIGN_IF = []
        CHARACTER_DESIGN_IF.extend(
            self.random_weighted(
                [
                    (DataSelector.CHARACTER_DESIGN.FANTASY_JOB, 20),
                    (DataSelector.CHARACTER_DESIGN.REALISTIC_JOB, 20),
                    (DataSelector.CHARACTER_DESIGN.NON_HUMAN, 20),
                    (DataSelector.CHARACTER_DESIGN.NON_HUMAN_SPECIES, 20),
                    (DataSelector.CHARACTER_DESIGN.MACHINERY, 20),
                    (DataSelector.CHARACTER_DESIGN.OTHER, 5),
                    (None, 150),
                ]
            )
        )
        CHARACTER_DESIGN_IF.extend(
            self.random_weighted(
                [
                    (DataSelector.CHARACTER_DESIGN.AGE, 15),
                    (DataSelector.CHARACTER_DESIGN.SKIN, 5),
                    (DataSelector.CHARACTER_DESIGN.PERSONALITY, 30),
                    (None, 70),
                ]
            )
        )
        ACCESSORIES_IF = []
        DAILY_ACCESSORIES = [
            (DataSelector.ACCESSORIES.HEAD, 20),
            (DataSelector.ACCESSORIES.EAR_DECORATIONS, 20),
            (DataSelector.ACCESSORIES.GLOVES, 15),
            (DataSelector.ACCESSORIES.ARM_WRIST, 20),
            (DataSelector.ACCESSORIES.WAIST, 15),
            (DataSelector.ACCESSORIES.LEG_FOOT, 15),
            (DataSelector.ACCESSORIES.NECK_DECORATIONS, 20),
            (None, 25)
        ]
        SPECIAL_OCCASION_ACCESSORIES = [
            (DataSelector.ACCESSORIES.THEME_DECORATIONS, 15),
            (DataSelector.ACCESSORIES.INSTRUMENTS, 15),
            (DataSelector.ACCESSORIES.SPORTS, 15),
            (DataSelector.ACCESSORIES.OTHER1, 15),
            (DataSelector.ACCESSORIES.OTHER2, 15),
            (DataSelector.ACCESSORIES.OTHER3, 15),
            (None, 70)
        ]
        KITCHEN_ACCESSORIES = [
            (DataSelector.ACCESSORIES.KITCHENWARE, 15),
            (DataSelector.ACCESSORIES.TABLEWARE, 15),
            (DataSelector.ACCESSORIES.FOOD, 15),
            (DataSelector.ACCESSORIES.SOUP_AND_DRINKS, 15),
            (DataSelector.ACCESSORIES.CONDIMENTS_AND_SAUCE, 15),
            (DataSelector.ACCESSORIES.MEAT_POULTRY_AND_EGGS, 10),
            (DataSelector.ACCESSORIES.FISH_AND_SEAFOOD, 10),
            (DataSelector.ACCESSORIES.DESSERTS, 10),
            (None, 45)
        ]
        OTHER_ACCESSORIES = [
            (DataSelector.ACCESSORIES.WEAPONS, 10),
            (DataSelector.ACCESSORIES.TOYS, 10),
            (DataSelector.ACCESSORIES.DIGITAL, 10),
            (DataSelector.ACCESSORIES.STATIONERY, 10),
            (DataSelector.ACCESSORIES.MATERIALS, 10),
            (DataSelector.ACCESSORIES.OTHER4, 10),
            (None, 140)
        ]
        ACCESSORIES_IF.extend(
            self.random_weighted(
                SPECIAL_OCCASION_ACCESSORIES
            )
        )
        if self.check_list_empty(ACCESSORIES_IF):
            ACCESSORIES_IF.extend(
                self.random_weighted(
                    DAILY_ACCESSORIES
                )
            )
        if self.check_list_empty(ACCESSORIES_IF):
            ACCESSORIES_IF.extend(
                self.random_weighted(
                    KITCHEN_ACCESSORIES
                )
            )
        ACCESSORIES_IF.extend(
            self.random_weighted(
                OTHER_ACCESSORIES
            )
        )
        CLOTHING_IF = []
        SPECIAL_OCCASION_CLOTHING = [
            (DataSelector.CLOTHING.HOLIDAY, 12),
            (DataSelector.CLOTHING.JOB_COSPLAY, 12),
            (DataSelector.CLOTHING.RACE_COSPLAY, 12),
            (DataSelector.CLOTHING.SPORTS, 12),
            (None, 152)
        ]
        TOP_CLOTHING = [
            (DataSelector.CLOTHING.TOP, 15),
            (DataSelector.CLOTHING.UNDERWEAR, 15),
            (DataSelector.CLOTHING.JACKET, 15),
            (DataSelector.CLOTHING.SWEATER, 15),
            (DataSelector.CLOTHING.SHIRT, 15),
            (DataSelector.CLOTHING.HOODIE, 15),
            (DataSelector.CLOTHING.COAT, 15),
            (DataSelector.CLOTHING.VEST, 15),
            (None, 120)
        ]
        BOTTOM_CLOTHING = [
            (DataSelector.CLOTHING.BOTTOM, 15),
            (DataSelector.CLOTHING.PANTIES, 15),
            (DataSelector.CLOTHING.SOCK, 15),
            (DataSelector.CLOTHING.PANTS, 15),
            (DataSelector.CLOTHING.SKIRT, 15),
            (None, 120)
        ]
        FULLBODY_CLOTHING = [
            (DataSelector.CLOTHING.OVERALL, 20),
            (DataSelector.CLOTHING.SWIMSUIT, 20),
            (DataSelector.CLOTHING.BIKINI, 20),
            (DataSelector.CLOTHING.KIMONO, 20),
            (DataSelector.CLOTHING.DRESS, 20),
            (DataSelector.CLOTHING.HAN_CLOTHING, 20),
            (DataSelector.CLOTHING.LOLITA, 15),
            (DataSelector.CLOTHING.UNIFORM, 15),
            (None, 50)
        ]
        SHOE_CLOTHING = [
            (DataSelector.CLOTHING.SHOES, 20),
            (None, 180)
        ]
        CLOTHING_IF.extend(
            self.random_weighted(
                SPECIAL_OCCASION_CLOTHING
            )
        )
        if self.check_list_empty(COMPOSITION_IF):
            CLOTHING_IF.extend(
                self.random_weighted(
                    TOP_CLOTHING
                )
            )
            CLOTHING_IF.extend(
                self.random_weighted(
                    BOTTOM_CLOTHING
                )
            )
            if self.check_list_empty(CLOTHING_IF):
                CLOTHING_IF.extend(
                    self.random_weighted(
                        FULLBODY_CLOTHING
                    )
                )
        CLOTHING_IF.extend(
            self.random_weighted(
                SHOE_CLOTHING
            )
        )
        BODY_IF = []
        HEAD_HAIRSTYLE = [
            (DataSelector.BODY.SIDE_HAIR, 15),
            (DataSelector.BODY.BANGS, 15),
            (DataSelector.BODY.HAIR_BUN, 15),
            (DataSelector.BODY.OVERALL_HAIRSTYLE, 20),
            (DataSelector.BODY.SPECIAL_EARS, 15),
            (DataSelector.BODY.HORN, 10),
            (DataSelector.BODY.BRAID, 15),
            (DataSelector.BODY.PONYTAIL, 15),
            (None, 100)
        ]
        HAIR_FEATURES = [
            (DataSelector.BODY.HAIR_QUALITY, 20),
            (DataSelector.BODY.HAIR_VOLUME, 20),
            (DataSelector.BODY.LENGTH, 20),
            (DataSelector.BODY.COLOR, 20),
            (None, 200)
        ]
        BODY_FEATURES = [
            (DataSelector.BODY.HAND, 20),
            (DataSelector.BODY.SHOULDER, 20),
            (DataSelector.BODY.CHEST, 20),
            (DataSelector.BODY.WAIST, 20),
            (DataSelector.BODY.ABDOMEN, 20),
            (DataSelector.BODY.HIP, 20),
            (DataSelector.BODY.LEG, 20),
            (DataSelector.BODY.FOOT, 20),
            (None, 100)
        ]
        DECORATIONS_AND_SPECIAL_FEATURES = [
            (DataSelector.BODY.OTHER, 20),
            (DataSelector.BODY.OTHER_DECORATIONS, 20),
            (DataSelector.BODY.ANIMAL_EARS, 20),
            (DataSelector.BODY.PATTERN, 20),
            (DataSelector.BODY.NECK_BACK, 20),
            (None, 100)
        ]
        BODY_IF.extend(
            self.random_weighted(
                HEAD_HAIRSTYLE
            )
        )
        if not self.check_list_empty(BODY_IF):
            BODY_IF.extend(
                self.random_weighted(
                    HAIR_FEATURES
                )
            )
        BODY_IF.extend(
            self.random_weighted(
                BODY_FEATURES
            )
        )
        if not self.check_list_empty(BODY_IF):
            BODY_IF.extend(
                self.random_weighted(
                    DECORATIONS_AND_SPECIAL_FEATURES
                )
            )

        FACE_IF = []
        PRIMARY_FACE_FEATURES = [
            (DataSelector.FACE.EYEBROWS, 15),
            (DataSelector.FACE.EYE_REGION, 15),
            (DataSelector.FACE.PUPIL_SHAPE, 15),
            (DataSelector.FACE.MOUTH, 15),
            (None, 140)
        ]
        DECORATIONS_AND_COLOR = [
            (DataSelector.FACE.EMBELLISHMENT, 15),
            (DataSelector.FACE.COLOR, 15),
            (DataSelector.FACE.EYE_DECORATION, 15),
            (None, 155)
        ]
        OTHER_FEATURES = [
            (DataSelector.FACE.FOREHEAD, 15),
            (DataSelector.FACE.OVERALL, 15),
            (DataSelector.FACE.OTHER, 15),
            (None, 155)
        ]
        FACE_IF.extend(
            self.random_weighted(
                PRIMARY_FACE_FEATURES
            )
        )
        if not self.check_list_empty(FACE_IF):
            FACE_IF.extend(
                self.random_weighted(
                    DECORATIONS_AND_COLOR
                )
            )
        FACE_IF.extend(
            self.random_weighted(
                OTHER_FEATURES
            )
        )
        EXPRESSION_IF = []
        BASIC_EXPRESSIONS = [
            (DataSelector.EXPRESSION.JOY, 15),
            (DataSelector.EXPRESSION.SADNESS, 15),
            (DataSelector.EXPRESSION.ANGER, 15),
            (DataSelector.EXPRESSION.SURPRISE, 15),
            (DataSelector.EXPRESSION.PANIC, 15),
            (DataSelector.EXPRESSION.TIRED, 15),
            (DataSelector.EXPRESSION.SHY, 15),
            (None, 200)
        ]
        EYE_AND_MOUTH_EXPRESSIONS = [
            (DataSelector.EXPRESSION.EYE, 50),
            (DataSelector.EXPRESSION.MOUTH, 50),
            (None, 100)
        ]
        EXPRESSION_IF.extend(
            self.random_weighted(
                BASIC_EXPRESSIONS
            )
        )
        EXPRESSION_IF.extend(
            self.random_weighted(
                EYE_AND_MOUTH_EXPRESSIONS
            )
        )
        COMPOSITION_IF = [i for i in COMPOSITION_IF if i is not None]
        SCENE_IF = [i for i in SCENE_IF if i is not None]
        ENVIRONMENT_IF = [i for i in ENVIRONMENT_IF if i is not None]
        BACKGROUND_IF = [i for i in BACKGROUND_IF if i is not None]
        R18_IF = [i for i in R18_IF if i is not None]
        ACTION_IF = [i for i in ACTION_IF if i is not None]
        ART_STYLE_IF = [i for i in ART_STYLE_IF if i is not None]
        ILLUSTRATOR_IF = [i for i in ILLUSTRATOR_IF if i is not None]
        CHARACTER_DESIGN_IF = [i for i in CHARACTER_DESIGN_IF if i is not None]
        ACCESSORIES_IF = [i for i in ACCESSORIES_IF if i is not None]
        CLOTHING_IF = [i for i in CLOTHING_IF if i is not None]
        BODY_IF = [i for i in BODY_IF if i is not None]
        FACE_IF = [i for i in FACE_IF if i is not None]
        EXPRESSION_IF = [i for i in EXPRESSION_IF if i is not None]

        ALL_IF = [
            *COMPOSITION_IF, *SCENE_IF, *ENVIRONMENT_IF, *BACKGROUND_IF, *R18_IF, *ACTION_IF, *ART_STYLE_IF,
            *ILLUSTRATOR_IF, *CHARACTER_DESIGN_IF, *ACCESSORIES_IF, *CLOTHING_IF, *BODY_IF, *FACE_IF,
            *EXPRESSION_IF
        ]
        # 逻辑组
        if num_of_characters == 1:
            _tag.append(f"{num_of_characters}{gender}")
        else:
            _tag.append(f"{num_of_characters}{gender}s")
        if enable_nsfw:
            _tag.append("nsfw")
        if DataSelector.COMPOSITION in self.pool or len(self.pool) == 0:
            for if_sub in COMPOSITION_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.COMPOSITION,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.SCENE in self.pool or len(self.pool) == 0:
            for if_sub in SCENE_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.SCENE,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.ENVIRONMENT in self.pool or len(self.pool) == 0:
            for if_sub in ENVIRONMENT_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.ENVIRONMENT,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.BACKGROUND in self.pool or len(self.pool) == 0:
            for if_sub in BACKGROUND_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.BACKGROUND,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.R18 in self.pool or len(self.pool) == 0:
            for if_sub in R18_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.R18,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.ACTION in self.pool or len(self.pool) == 0:
            for if_sub in ACTION_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.ACTION,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.ART_STYLE in self.pool or len(self.pool) == 0:
            for if_sub in ART_STYLE_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.ART_STYLE,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.ILLUSTRATOR in self.pool or len(self.pool) == 0:
            for if_sub in ILLUSTRATOR_IF:
                tags = self.random_tag(
                    top_type=DataSelector.ILLUSTRATOR,
                    sub_type=if_sub,
                    n=1
                )
                for tag in tags:
                    if isinstance(tag, tuple):
                        _tag.append(("{" + self.enhance_tag(tag[0]) + "}", tag[1]))
                    elif isinstance(tag, str):
                        _tag.append(self.enhance_tag(tag))
        if DataSelector.CHARACTER_DESIGN in self.pool or len(self.pool) == 0:
            for if_sub in CHARACTER_DESIGN_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.CHARACTER_DESIGN,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.ACCESSORIES in self.pool or len(self.pool) == 0:
            for if_sub in ACCESSORIES_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.ACCESSORIES,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.CLOTHING in self.pool or len(self.pool) == 0:
            for if_sub in CLOTHING_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.CLOTHING,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.BODY in self.pool or len(self.pool) == 0:
            for if_sub in BODY_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.BODY,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.FACE in self.pool or len(self.pool) == 0:
            for if_sub in FACE_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.FACE,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.EXPRESSION in self.pool or len(self.pool) == 0:
            for if_sub in EXPRESSION_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.EXPRESSION,
                    sub_type=if_sub,
                    n=1
                ))
        if DataSelector.COMPOSITION in self.pool or len(self.pool) == 0:
            for if_sub in COMPOSITION_IF:
                _tag.extend(self.random_tag(
                    top_type=DataSelector.COMPOSITION,
                    sub_type=if_sub,
                    n=1
                ))
        _cleaned_tag = []
        # 遍历tag,将其中的tuple,提取第一个元素
        for i, t in enumerate(_tag):
            if isinstance(t, tuple):
                _cleaned_tag.append(t[0])
            else:
                _cleaned_tag.append(t)
        return _tag, _cleaned_tag
