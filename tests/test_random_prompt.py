# -*- coding: utf-8 -*-
# @Time    : 2024/1/27 上午10:41
# @Author  : sudoskys
# @File    : test_random_prompt.py
# @Software: PyCharm

from src.novelai_python.utils.random_prompt import RandomPromptGenerator


def test_generate_returns_string():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result = generator.generate()
    assert isinstance(result, str)


def test_generate_returns_non_empty_string():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result = generator.generate()
    assert len(result) > 0


def test_generate_returns_different_results():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result1 = generator.generate()
    result2 = generator.generate()
    assert result1 != result2


def test_generate_with_nsfw_disabled():
    generator = RandomPromptGenerator(nsfw_enabled=False)
    result = generator.generate()
    assert 'nsfw' not in result


def test_generate_with_nsfw_enabled():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result = generator.generate()
    assert 'nsfw' in result


def test_get_weighted_choice_returns_string():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result = generator.get_weighted_choice([['tag1', 1], ['tag2', 2]], [])
    assert isinstance(result, str)


def test_get_weighted_choice_returns_valid_tag():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result = generator.get_weighted_choice([['tag1', 1], ['tag2', 2]], [])
    assert result in ['tag1', 'tag2']


def test_character_features_returns_list():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result = generator.character_features('m', 'front', True, 1)
    assert isinstance(result, list)


def test_character_features_returns_non_empty_list():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result = generator.character_features('m', 'front', True, 1)
    assert len(result) > 0


def test_character_features_with_different_genders():
    generator = RandomPromptGenerator(nsfw_enabled=True)
    result_m = generator.character_features('m', 'front', True, 1)
    result_f = generator.character_features('f', 'front', True, 1)
    result_o = generator.character_features('o', 'front', True, 1)
    assert result_m != result_f != result_o
