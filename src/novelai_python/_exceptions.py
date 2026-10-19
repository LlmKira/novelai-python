# @Time    : 2024/1/26 上午10:55
# @Author  : sudoskys
# @File    : _exceptions.py

from typing import Any


class NovelAiError(Exception):
    """
    NovelAiError is the base exception for all novelai_python errors.
    """

    message: str

    def __init__(self, message: str) -> None:
        self.message = message

    # error.__dict__ is the public way to serialize an error (server.py, users); kept as is
    @property
    def __dict__(self) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleVariableOverride]
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

    # raised `from` the transport error: name it (proxy 407, DNS failure, timeout...)
    def __str__(self) -> str:
        return f"{self.message} ({self.__cause__})" if self.__cause__ else self.message

    @property
    def __dict__(self) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleVariableOverride]
        return {"message": str(self)}


class APIError(NovelAiError):
    """
    APIError is raised when the API returns an error.
    """

    request: Any
    code: int | str | None = None
    response: dict[str, Any] | str | None = None

    def __init__(
        self, message: str, request: Any, response: dict[str, Any] | str | None, code: int | str | None
    ) -> None:
        super().__init__(message)
        self.request = request
        self.response = response
        self.code = code

    def __reduce__(self):
        # pickle (multiprocessing, task queues) rebuilds from args, which hold only the message
        return self.__class__, (self.message, self.request, self.response, self.code)

    @property
    def __dict__(self) -> dict[str, Any]:
        parent_dict = super().__dict__
        parent_dict.update({"request": self.request, "response": self.response, "code": self.code})
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


class DailyLimitExceeded(NovelAiError):
    """
    DailyLimitExceeded is raised locally, before any request is sent,
    when the configured per-window image budget is used up.
    """

    limit: int
    used: int
    reset_at: float

    def __init__(self, message: str, *, limit: int, used: int, reset_at: float) -> None:
        super().__init__(message)
        self.limit = limit
        self.used = used
        self.reset_at = reset_at

    @property
    def __dict__(self) -> dict[str, Any]:
        parent_dict = super().__dict__
        parent_dict.update(
            {
                "limit": self.limit,
                "used": self.used,
                "reset_at": self.reset_at,
            }
        )
        return parent_dict
