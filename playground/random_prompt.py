# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:51
# @Author  : sudoskys
# @File    : random_prompt.py
# @Software: PyCharm
import random

from novelai_python.utils.random_prompt import RandomPromptGenerator


print(random.random())
s = RandomPromptGenerator(nsfw_enabled=True).generate()
print(s)
