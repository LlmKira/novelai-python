"""Retry for NovelAI requests that failed with HTTP 500 (replaces tenacity)."""

import asyncio
import functools
import random
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

__all__ = ["retry_on_server_error"]


def _is_server_error(exc: BaseException) -> bool:
    return str(getattr(exc, "code", "")) == "500"


def retry_on_server_error(
    attempts: int = 3, min_wait: float = 1.0, max_wait: float = 3.0
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """Retry an ``async def`` call up to ``attempts`` times while it raises an error with ``code == 500``.

    Only server errors are retried: transport errors are not, because the request may already
    have been accepted (and charged) by NovelAI. Do not use on async generators: a stream that
    has already yielded data cannot be replayed safely.
    """

    def decorator(fn: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(1, attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    if attempt == attempts or not _is_server_error(exc):
                        raise
                    await asyncio.sleep(random.uniform(min_wait, max_wait))
            raise AssertionError("unreachable")

        return wrapper

    return decorator
