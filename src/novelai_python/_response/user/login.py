# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午11:57
# @Author  : sudoskys
# @File    : login.py


from ..schema import RespBase


class LoginResp(RespBase):
    accessToken: str
