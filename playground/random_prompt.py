# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:51
# @Author  : sudoskys
# @File    : random_prompt.py


from novelai_python.tool.random_prompt import RandomPromptGenerator

gen = RandomPromptGenerator(nsfw_enabled=True)
print(gen.get_weighted_choice([[1, 35], [2, 20], [3, 7]], []))
print("====")
print(gen.get_weighted_choice([['mss', 30], ['fdd', 50], ['oa', 10]], []))
print("====")
print(gen.get_weighted_choice([['m', 30], ['f', 50], ['o', 10]], ['m']))
print("====")
for i in range(200):
    s = RandomPromptGenerator(nsfw_enabled=True).random_prompt()
    print(s)
