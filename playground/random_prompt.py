# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:51
# @Author  : sudoskys
# @File    : random_prompt.py


from novelai_python.tool.random_prompt import RandomPromptGenerator

gen = RandomPromptGenerator()
for i in range(200):
    s = RandomPromptGenerator()
    print(s.generate_common_tags(nsfw=False))
    print(s.generate_scene_tags())
    print(s.generate_scene_composition())
    print(s.get_holiday_themed_tags())
    print(s.generate_character(
        tags=["vampire", "werewolf"],
        gender="f",
        additional_tags="",
        character_limit=1,
    ))
    print(s.generate_character_traits(
        gender="f",
        portrait_type="half-length portrait",
        level=1
    ))
