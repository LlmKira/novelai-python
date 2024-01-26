# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午10:55
# @Author  : sudoskys
# @File    : _exceptions.py
# @Software: PyCharm
from typing import Any, Optional, Union
from typing import TypeGuard


def is_dict(obj: object) -> TypeGuard[dict[object, object]]:
    """
    Check if the object is a dict.
    :param obj:  The object to check.
    :return:   True if the object is a dict, False otherwise.
    """
    return isinstance(obj, dict)


class NovelAiError(Exception):
    """
    NovelAiError is the base exception for all novelai_python errors.
    """
    pass


class APIError(NovelAiError):
    """
    APIError is raised when the API returns an error.
    """
    message: str
    request: Any
    code: Optional[str] = None
    response: Union[dict[str, Any], str] = None

    def __init__(self, message: str, request: Any, response: Any, status_code: str) -> None:
        super().__init__(message)
        self.request = request
        self.message = message
        self.code = status_code
        self.response = response


class AuthError(APIError):
    """
    AuthError is raised when the API returns an error.
    """

    def __init__(self, message: str, request: Any, response: Any, status_code: str) -> None:
        super().__init__(message, request, response, status_code)
