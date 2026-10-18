import random
from collections.abc import Sequence
from typing import Any

from pydantic import dataclasses

from .data.anime_v4_data import (
    ACCESSORIES_V4,
    ANGLES_V4,
    BACKGROUNDS_V4,
    BODY_FEATURES_V4,
    BODYSUITS_V4,
    BOTTOMS_V4,
    CHEST_V4,
    COLORS_V4,
    DRESSES_V4,
    EFFECTS_V4,
    EXPRESSIONS_V4,
    EYE_COLORS_V4,
    EYES_EXPR_V4,
    EYES_V4,
    FOCUS_V4,
    FRAMING_V4,
    HAIR_BANGS_V4,
    HAIR_COLORS_SPECIAL_V4,
    HAIR_COLORS_V4,
    HAIR_LENGTH_V4,
    HAIR_STYLE_V4,
    HAIR_TYPE_V4,
    HAT_EXTRAS_V4,
    HATS_V4,
    HEAD_ACCESSORIES_V4,
    OBJECTS_V4,
    POSES_V4,
    SCENERY_DETAILS_V4,
    SCENERY_TYPES_V4,
    SHOES_V4,
    SKIN_V4,
    SOCKS_EXTRAS_V4,
    SOCKS_V4,
    SPECIES_V4,
    STYLES_V4,
    SWIMSUITS_V4,
    TOPS_V4,
    UNIFORMS_V4,
    YEARS_V4,
)
from .logic import pick_option

WeightedOption = tuple[str, int, list, list, list]
WeightedSimpleOption = list[int]
WeightedOptions = list[WeightedOption]
WeightedSimpleOptions = list[WeightedSimpleOption]

# The tag tables live in data/anime_v4_data; the names below are the ones this module used.
cameraAnglesL = ANGLES_V4
framingTypesL = FRAMING_V4
subjectFocusL = FOCUS_V4
sceneTypesL = SCENERY_TYPES_V4
backgroundTypesL = BACKGROUNDS_V4
artStylesL = STYLES_V4
animalCharacteristicsL = SPECIES_V4
skinTypesL = SKIN_V4
eyeCharacteristicsL = EYES_V4
eyeExpressionsL = EYES_EXPR_V4
hairLengthsL = HAIR_LENGTH_V4
braidedHairstylesL = HAIR_STYLE_V4
uniqueHairstylesL = HAIR_TYPE_V4
bangsStylesL = HAIR_BANGS_V4
breastSizesL = CHEST_V4
bodyFeaturesL = BODY_FEATURES_V4
hatsAndHeadwearL = HATS_V4
hairAccessoriesL = HEAD_ACCESSORIES_V4
hatDecorationsL = HAT_EXTRAS_V4
dressesAndAttireL = DRESSES_V4
socksAndStockingsL = SOCKS_V4
legwearStylesL = SOCKS_EXTRAS_V4
topsAndShirtsL = TOPS_V4
pantsAndBottomsL = BOTTOMS_V4
bootsAndFootwearL = SHOES_V4
armorsAndUniformsL = UNIFORMS_V4
zipperedOutfitsL = BODYSUITS_V4
swimwearL = SWIMSUITS_V4
accessoriesAndOuterwearL = ACCESSORIES_V4
facialExpressionsL = EXPRESSIONS_V4
yearlyThemesL = YEARS_V4
sceneElementsL = SCENERY_DETAILS_V4
objectsAndStuffedAnimalsL = OBJECTS_V4
bodyPosesAndActionsL = POSES_V4
effectsAndPatternsL = EFFECTS_V4
eyeColorsL = EYE_COLORS_V4
hairColorsL = HAIR_COLORS_V4
hairStylesAndPatternsL = HAIR_COLORS_SPECIAL_V4
colorsL = COLORS_V4


@dataclasses.dataclass
class Conditions:
    tags: list[str]

    def add(self, v: str) -> None:
        if v not in self.tags:
            self.tags.append(v)

    def __contains__(self, item) -> bool:
        return item in self.tags

    def copy(self):
        tags = list(set(self.tags))
        return Conditions(tags.copy())


def random_range(a, b):
    if a == b:
        return a
    if a > b:
        a, b = b, a
    return random.randint(a, b)


def select_weighted_option(
    options: Sequence[Sequence[Any]],
    conditions: Conditions,
) -> str | int:
    """
    选择一个加权选项: a row is skipped when one of its exclusions ([4]) is a condition or one of
    its requirements ([3]) is missing; the picked row adds what it provides ([2]).
    :param options: 权重
    :param conditions: 条件
    :return: 选项
    """
    return pick_option(options, conditions)


def select_weighted_count(options: Sequence[Sequence[Any]], conditions: Conditions) -> int:
    """select_weighted_option for tables whose values are counts."""
    return int(select_weighted_option(options, conditions) or 0)


def generate_appearance(
    tags: Conditions, gender: str, additional_tags: str | None, character_limit: int
) -> list[str | int]:
    """
    为人物生成外貌描述
    :param tags: 已有标签
    :param gender: 性别
    :param additional_tags: 额外标签
    :param character_limit: 人物数量
    :return: 外貌描述
    """
    selected_attributes = []
    uni_tags = tags.copy()

    if random.random() < 0.1:
        selected_attributes.append(select_weighted_option(animalCharacteristicsL, uni_tags))
    if random.random() < 0.4:
        selected_attributes.append(select_weighted_option(skinTypesL, uni_tags))
    if random.random() < 0.05:
        selected_attributes.append(select_weighted_option(eyeCharacteristicsL, uni_tags))
    if "no eyes" not in uni_tags:
        if random.random() < 0.2:
            selected_attributes.append(select_weighted_option(eyeExpressionsL, uni_tags))
        if random.random() < 0.8 and "nocoloreyes" not in uni_tags:
            selected_attributes.append(select_weighted_option(eyeColorsL, uni_tags))
    # Hair Length
    if random.random() < 0.8:
        selected_attributes.append(select_weighted_option(hairLengthsL, uni_tags))

    # Hair Style
    if random.random() < 0.7:
        selected_attributes.append(select_weighted_option(braidedHairstylesL, uni_tags))

    # Hair Color
    if random.random() < 0.7:
        selected_attributes.append(select_weighted_option(hairColorsL, uni_tags))

    # Hair Style and Pattern
    if random.random() < 0.1:
        selected_attributes.append(select_weighted_option(hairStylesAndPatternsL, uni_tags))
        selected_attributes.append(select_weighted_option(hairColorsL, uni_tags))

    # Hair Accessories
    if random.random() < 0.3:
        selected_attributes.append(select_weighted_option(uniqueHairstylesL, uni_tags))

    # Hair Accessories
    if random.random() < 0.4:
        selected_attributes.append(select_weighted_option(bangsStylesL, uni_tags))
    if gender.startswith("f") and random.random() < 0.8:
        selected_attributes.append(select_weighted_option(breastSizesL, uni_tags))

    if character_limit == 1:
        body_feature_num = select_weighted_count(
            [
                [0, 10],
                [1, 30],
                [2, 15],
                [3, 5],
            ],
            uni_tags,
        )
    elif character_limit == 2:
        body_feature_num = select_weighted_count(
            [
                [0, 20],
                [1, 40],
                [2, 10],
            ],
            uni_tags,
        )
    else:
        body_feature_num = select_weighted_count(
            [
                [0, 30],
                [1, 30],
            ],
            uni_tags,
        )

    for _ in range(body_feature_num):
        selected_attributes.append(select_weighted_option(bodyFeaturesL, uni_tags))

    if random.random() < 0.2:
        selected_attributes.append(select_weighted_option(hatsAndHeadwearL, uni_tags))
        if random.random() < 0.2:
            selected_attributes.append(select_weighted_option(hatDecorationsL, uni_tags))
    elif random.random() < 0.3:
        selected_attributes.append(select_weighted_option(hairAccessoriesL, uni_tags))

    outfit_type = select_weighted_option(
        [
            ["uniform", 25],
            ["swimsuit", 5],
            ["bodysuit", 5],
            ["normal clothes", 40],
        ],
        uni_tags,
    )

    if outfit_type == "uniform":
        selected_attributes.append(select_weighted_option(armorsAndUniformsL, uni_tags))
    elif outfit_type == "swimsuit":
        selected_attributes.append(select_weighted_option(swimwearL, uni_tags))
    elif outfit_type == "bodysuit":
        selected_attributes.append(select_weighted_option(zipperedOutfitsL, uni_tags))
    elif outfit_type == "normal clothes":
        # 生产袜子
        if gender.startswith("f") and random.random() < 0.5:
            selected_attributes.append(select_weighted_option(socksAndStockingsL, uni_tags))
            if random.random() < 0.2:
                selected_attributes.append(select_weighted_option(legwearStylesL, uni_tags))
        # 生产套装
        if gender.startswith("f") and random.random() < 0.2:
            use_color = random.random() < 0.5
            color = select_weighted_option(colorsL, uni_tags)
            attire = select_weighted_option(dressesAndAttireL, uni_tags)
            selected_attributes.append(f"{color} {attire}" if use_color and attire else attire)
        else:
            # 生产上衣
            if random.random() < 0.85:
                use_color = random.random() < 0.5
                color = select_weighted_option(colorsL, uni_tags)
                top = select_weighted_option(topsAndShirtsL, uni_tags)
                selected_attributes.append(f"{color} {top}" if use_color and top else top)
            # 生产下衣
            if "legs" in uni_tags:
                if random.random() < 0.85:
                    use_color = random.random() < 0.5
                    color = select_weighted_option(colorsL, uni_tags)
                    bottom = select_weighted_option(pantsAndBottomsL, uni_tags)
                    selected_attributes.append(f"{color} {bottom}" if use_color and bottom else bottom)
                # 生产鞋子
                if "feet" in uni_tags and random.random() < 0.6:
                    use_color = random.random() < 0.5
                    color = select_weighted_option(colorsL, uni_tags)
                    footwear = select_weighted_option(bootsAndFootwearL, uni_tags)
                    selected_attributes.append(f"{color} {footwear}" if use_color and footwear else footwear)

    # 生产面部
    if random.random() < 0.6:
        selected_attributes.append(select_weighted_option(facialExpressionsL, uni_tags))

    # 生产动作
    if random.random() < 0.4:
        selected_attributes.append(select_weighted_option(bodyPosesAndActionsL, uni_tags))

    # 根据人物数量生产配饰
    if character_limit == 1:
        accessory_iterations = select_weighted_count(
            [
                [0, 10],
                [1, 30],
                [2, 15],
                [3, 5],
            ],
            uni_tags,
        )
    elif character_limit == 2:
        accessory_iterations = select_weighted_count(
            [
                [0, 20],
                [1, 40],
                [2, 10],
            ],
            uni_tags,
        )
    else:
        accessory_iterations = select_weighted_count(
            [
                [0, 30],
                [1, 30],
            ],
            uni_tags,
        )

    for _ in range(accessory_iterations):
        selected_attributes.append(select_weighted_option(accessoriesAndOuterwearL, uni_tags))

    return [attribute for attribute in selected_attributes if attribute != ""]


def generate_scene_composition():
    scene_tags = []
    condition_set = Conditions(tags=[])
    character_details = []

    character_count = select_weighted_count(
        [
            [1, 70],
            [2, 20],
            [3, 7],
            [0, 5],
        ],
        condition_set,
    )

    if character_count == 0:
        scene_tags.append("no humans")
        if random.random() < 0.5:
            scene_tags.append(select_weighted_option(artStylesL, condition_set))
        scene_tags.append(select_weighted_option(sceneTypesL, condition_set))

        scene_element_count = select_weighted_count(
            [
                [2, 15],
                [3, 50],
                [4, 15],
                [5, 5],
            ],
            condition_set,
        )

        for _ in range(scene_element_count):
            scene_tags.append(select_weighted_option(sceneElementsL, condition_set))

        object_count = select_weighted_count(
            [
                [0, 15],
                [1, 10],
                [2, 20],
                [3, 20],
                [4, 20],
                [5, 15],
            ],
            condition_set,
        )
        object_count -= character_count
        object_count = max(0, object_count)

        for _ in range(object_count):
            scene_tags.append(select_weighted_option(objectsAndStuffedAnimalsL, condition_set))

        return [", ".join(str(tag) for tag in scene_tags if tag)]

    if random.random() < 0.5:
        scene_tags.append(select_weighted_option(artStylesL, condition_set))

    male_count = 0
    female_count = 0
    other_count = 0

    for _ in range(character_count):
        gender = select_weighted_option(
            [
                ["m", 30],
                ["f", 60],
                ["o", 0],
            ],
            condition_set,
        )
        if gender == "m":
            male_count += 1
        elif gender == "f":
            female_count += 1
        elif gender == "o":
            other_count += 1

    if female_count >= 1:
        scene_tags.insert(0, f"{female_count}girl{'s' if female_count > 1 else ''}")
    if male_count >= 1:
        scene_tags.insert(0, f"{male_count}boy{'s' if male_count > 1 else ''}")
    if other_count >= 1:
        scene_tags.insert(0, f"{other_count}other{'s' if other_count > 1 else ''}")

    if random.random() < 0.8:
        background_type = select_weighted_option(backgroundTypesL, condition_set)
        scene_tags.append(background_type)
        if background_type == "scenery" and random.random() < 0.5:
            scenery_elements_count = random.randint(1, 3)
            for _ in range(scenery_elements_count):
                # Add scenery elements
                scene_tags.append(select_weighted_option(sceneElementsL, condition_set))

    # 添加镜头角度
    if random.random() < 0.3:
        scene_tags.append(select_weighted_option(cameraAnglesL, condition_set))

    # 添加镜头构图
    framing_type = str(select_weighted_option(framingTypesL, condition_set)) if random.random() < 0.7 else None
    if framing_type:
        scene_tags.append(framing_type)

    # Gender is a condition the tag tables use (e.g. "rabbit girl" requires "female").
    # Give each character its own copy so a male character does not inherit "female".
    for _ in range(female_count):
        character_conditions = condition_set.copy()
        character_conditions.add("female")
        female_appearance = [
            "girl",
            *generate_appearance(character_conditions, "f", framing_type, character_count),
        ]
        character_details.append(female_appearance)

    for _ in range(male_count):
        character_conditions = condition_set.copy()
        character_conditions.add("male")
        male_appearance = ["boy", *generate_appearance(character_conditions, "m", framing_type, character_count)]
        character_details.append(male_appearance)

    for _ in range(other_count):
        # No "other" row in the tables requires a gender tag.
        other_appearance = ["other", *generate_appearance(condition_set, "o", framing_type, character_count)]
        character_details.append(other_appearance)

    # Scene-level rows such as "breast focus" require the scene to know its genders.
    if female_count:
        condition_set.add("female")
    if male_count:
        condition_set.add("male")

    # 添加场景元素
    if random.random() < 0.2:
        object_count = random.randint(0, 4)
        if character_count == 2:
            object_count = random.randint(0, 3)
        for _ in range(object_count):
            scene_tags.append(select_weighted_option(objectsAndStuffedAnimalsL, condition_set))

    # 添加特效
    if random.random() < 0.25:
        effects_count = random.randint(1, 3)
        for _ in range(effects_count):
            scene_tags.append(select_weighted_option(effectsAndPatternsL, condition_set))

    # 添加年份主题
    if random.random() < 0.2:
        scene_tags.append(select_weighted_option(yearlyThemesL, condition_set))

    # 添加物体焦点
    if random.random() < 0.1:
        scene_tags.append(select_weighted_option(subjectFocusL, condition_set))

    # 去重
    scene_tags = list({tag: True for tag in scene_tags}.keys())
    return [", ".join(map(str, scene_tags)), *[", ".join(map(str, details)) for details in character_details]]


if __name__ == "__main__":
    print(generate_scene_composition())
