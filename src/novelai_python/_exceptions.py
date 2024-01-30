# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午10:55
# @Author  : sudoskys
# @File    : _exceptions.py
# @Software: PyCharm
from typing import Any, Optional, Union, Dict


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
    response: Union[Dict[str, Any], str] = None

    def __init__(self, message: str, request: dict, response: Union[dict, str], status_code: str) -> None:
        if not isinstance(response, dict):
            response = {"error": f"data type error, should be dict, but got {type(response)}"}
        if not isinstance(request, dict):
            request = {"error": f"data type error, should be dict, but got {type(request)}"}
        self.request = request
        self.message = message
        self.code = status_code
        self.response = response


class AuthError(APIError):
    """
    AuthError is raised when the API returns an error.
    """

    def __init__(self, message: str, request: dict, response: Union[dict, str], status_code: str) -> None:
        super().__init__(message, request, response, status_code)
