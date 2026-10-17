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
    assert "nsfw" not in result


def test_generate_common_tags_nsfw():
    generator = RandomPromptGenerator()
    result = generator.generate_common_tags(nsfw=True)
    assert "nsfw" in result


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
    result = generator.generate_character_traits(gender="f", portrait_type="half-length portrait", level=3)
    assert len(result) > 0


def test_get_holiday_themed_tags():
    generator = RandomPromptGenerator()
    result_m = generator.get_holiday_themed_tags()
    result_f = generator.get_holiday_themed_tags()
    result_o = generator.get_holiday_themed_tags()
    assert len({result_m, result_f, result_o}) != 1


def test_selector_uses_provides_requires_excludes():
    """[2] is what a picked row provides, [3] what it requires, [4] what excludes it."""
    from novelai_python.tool.random_prompt.generate_scene_composition import select_weighted_option

    rows = [["foot focus", 12, [], ["feet"], []], ["hip focus", 12, [], [], ["front"]]]
    for _ in range(50):
        assert select_weighted_option(rows, set()) == "hip focus"
    assert select_weighted_option([rows[0]], {"feet"}) == "foot focus"
    assert select_weighted_option([rows[1]], {"front"}) == ""
    conditions: set[str] = set()
    assert select_weighted_option([["full body", 12, ["feet", "legs"], [], []]], conditions) == "full body"
    assert conditions == {"feet", "legs"}


def test_requirement_gated_rows_are_reachable():
    import random

    random.seed(0)
    prompts = [", ".join(RandomPromptGenerator.generate_scene_composition()) for _ in range(3000)]
    prompts += [
        ", ".join(map(str, RandomPromptGenerator.generate_character(tags=[], gender="f", character_limit=1)))
        for _ in range(3000)
    ]
    assert any("foot focus" in p for p in prompts)


def test_v2_generators_run_in_every_mode():
    import random

    from novelai_python.tool.random_prompt import RandomPromptGeneratorV2

    for model in ("anime_v3", "anime_v4", "furry"):
        for seed in range(100):
            random.seed(seed)
            for holiday in (False, True):
                for nsfw in (False, True):
                    prompt = RandomPromptGeneratorV2.generate(model=model, holiday=holiday, nsfw=nsfw)
                    assert isinstance(prompt, str) and prompt
