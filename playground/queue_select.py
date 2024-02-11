# -*- coding: utf-8 -*-
# @Time    : 2024/2/11 下午12:29
# @Author  : sudoskys
# @File    : queue_select.py
# @Software: PyCharm
from novelai_python.utils.useful import QueSelect

####
# This is a simple example of how to use the QueSelect class
# Even load tools
####

if __name__ == '__main__':
    q = QueSelect(['a', 'b'])
    print(q.get(1))
    # print(q.get(2))
    print(q.get(1))
    # print(q.get(2))
    print(q.get(1))
    # print(q.get(2))
    print(q.get(1))
    print(q.get(1))
    print(q.get(1))
    print(q.get(1))
    print(q.get(1))
    print(q.get(1))

