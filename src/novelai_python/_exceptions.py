# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 上午10:55
# @Author  : sudoskys
# @File    : _exceptions.py

from typing import Any, Union, Dict


class NovelAiError(Exception):
    """
    NovelAiError is the base exception for all novelai_python errors.
    """
    message: str

    def __init__(self, message: str) -> None:
        self.message = message

    @property
    def __dict__(self):
        return {
            "message": self.message,
        }


class InvalidRequestHeader(NovelAiError):
    """
    InvalidRequestHeader is raised when the request header is invalid.
    """
    pass


class SessionHttpError(NovelAiError):
    """
    HTTPError is raised when a request to the API fails.
    """
    pass


class APIError(NovelAiError):
    """
    APIError is raised when the API returns an error.
    """
    request: Any
    code: Union[str, None] = None
    response: Union[Dict[str, Any], str] = None

    def __init__(self,
                 message: str,
                 request: Any,
                 response: Union[Dict[str, Any], str],
                 code: Union[str, None]
                 ) -> None:
        super().__init__(message)
        self.request = request
        self.response = response
        self.code = code

    @property
    def __dict__(self):
        parent_dict = super().__dict__
        parent_dict.update({
            "request": self.request,
            "response": self.response,
            "code": self.code
        })
        return parent_dict


class ConcurrentGenerationError(APIError):
    """
    ConcurrentGenerationError is raised when the API returns an error.
    """

    pass


class DataSerializationError(APIError):
    """
    DataSerializationError is raised when the API data is not serializable.
    """

    pass


class AuthError(APIError):
    """
    AuthError is raised when the API returns an error.
    """

    pass
