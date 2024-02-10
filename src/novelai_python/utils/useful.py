# -*- coding: utf-8 -*-
# @Time    : 2024/2/9 下午10:41
# @Author  : sudoskys
# @File    : useful.py
# @Software: PyCharm
def enum_to_list(enum_):
    return list(map(lambda x: x.value, enum_._member_map_.values()))
