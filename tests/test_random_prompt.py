# -*- coding: utf-8 -*-
# @Time    : 2024/1/27 上午10:41
# @Author  : sudoskys
# @File    : test_random_prompt.py


from novelai_python.tool.random_prompt import RandomPromptGenerator


def test_generate_scene_tags():
    generator = RandomPromptGenerator()
    result = generator.generate_scene_tags()
    assert len(result) > 0


def test_generate_scene_composition():
    generator = RandomPromptGenerator()
    result1 = generator.generate_scene_composition()
    result2 = generator.generate_scene_composition()
    assert result1 != result2


def test_generate_common_tags_non_nsfw():
    generator = RandomPromptGenerator()
    result = generator.generate_common_tags(nsfw=False)
    assert 'nsfw' not in result


def test_generate_common_tags_nsfw():
    generator = RandomPromptGenerator()
    result = generator.generate_common_tags(nsfw=True)
    assert 'nsfw' in result


def test_generate_character():
    generator = RandomPromptGenerator()
    result = generator.generate_character(
        tags=["vampire", "werewolf"],
        gender="f",
        additional_tags="",
        character_limit=1,
    )
    assert isinstance(result, list)


def test_generate_character_traits():
    generator = RandomPromptGenerator()
    result = generator.generate_character_traits(
        gender="f",
        portrait_type="half-length portrait",
        level=3
    )
    assert len(result) > 0


def test_get_holiday_themed_tags():
    generator = RandomPromptGenerator()
    result_m = generator.get_holiday_themed_tags()
    result_f = generator.get_holiday_themed_tags()
    result_o = generator.get_holiday_themed_tags()
    assert len({result_m, result_f, result_o}) != 1
