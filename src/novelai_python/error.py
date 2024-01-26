# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午12:58
# @Author  : sudoskys
# @File    : error.py
# @Software: PyCharm


class ServerError(Exception):
    def __init__(self, msg: str = None):
        self.msg = msg

    def __str__(self):
        return f"ServerError: {self.msg}"


class ValidationError(Exception):
    def __init__(self, msg: str = None):
        self.msg = msg

    def __str__(self):
        return f"ValidationError: {self.msg}"


class AuthError(Exception):
    def __init__(self, msg: str = None):
        self.msg = msg

    def __str__(self):
        return f"AuthError: {self.msg}"
