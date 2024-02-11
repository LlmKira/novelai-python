# -*- coding: utf-8 -*-
# @Time    : 2024/2/9 下午10:41
# @Author  : sudoskys
# @File    : useful.py
# @Software: PyCharm
import collections
import random
from typing import List


def enum_to_list(enum_):
    return list(map(lambda x: x.value, enum_._member_map_.values()))


class QueSelect(object):
    def __init__(self, data: List[str]):
        """
        A queue selector
        :param data:
        """
        self.data = collections.deque(data)
        self.used = collections.deque()
        self.users = {}

    def get(self, user_id: int) -> str:
        if user_id not in self.users:
            self.users[user_id] = {'data': self.data.copy(), 'used': collections.deque()}

        user_data = self.users[user_id]['data']
        user_used = self.users[user_id]['used']

        if len(user_data) == 0:
            user_data, user_used = user_used, user_data
            # 随机掉 User data
            if len(user_data) > 2:
                random.shuffle(user_data)
            self.users[user_id]['data'] = user_data
            self.users[user_id]['used'] = user_used

        selected = user_data.popleft()
        user_used.append(selected)

        return selected


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
