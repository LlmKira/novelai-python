# @File    : daily_limit.py
"""
Local image budget: at most N images per rolling window (default 2500 / 24h).

The window is anchored at the first image generated after start-up (or after
the previous window expired), not at midnight. State is persisted to a JSON
file so the budget survives process restarts.

Disable with ``NOVELAI_DAILY_IMAGE_LIMIT=0`` or pass ``limiter=None``.
"""

import json
import os
import pathlib
import threading
import time

from loguru import logger

from .._exceptions import DailyLimitExceeded

DEFAULT_IMAGE_LIMIT = 2500
DEFAULT_WINDOW_SECONDS = 24 * 60 * 60
ENV_LIMIT = "NOVELAI_DAILY_IMAGE_LIMIT"
ENV_STATE_FILE = "NOVELAI_LIMIT_STATE_FILE"


class DailyImageLimiter:
    def __init__(
        self,
        limit: int = DEFAULT_IMAGE_LIMIT,
        *,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        state_file: str | pathlib.Path | None = None,
    ) -> None:
        """
        :param limit: images allowed per window; 0 or less disables the limiter
        :param window_seconds: window length, counted from the first image of the window
        :param state_file: where to persist the counter; None keeps it in memory only
        """
        self.limit = int(limit)
        self.window_seconds = int(window_seconds)
        self.state_file = pathlib.Path(state_file) if state_file else None
        self._lock = threading.Lock()
        self._window_start: float | None = None
        self._used = 0
        self._load()

    # region persistence
    def _load(self) -> None:
        if not self.state_file or not self.state_file.exists():
            return
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            self._window_start = data.get("window_start")
            self._used = int(data.get("used", 0))
        except Exception as e:
            logger.warning(f"Failed to read limiter state {self.state_file}: {e}, starting fresh")
            self._window_start, self._used = None, 0

    def _save(self) -> None:
        if not self.state_file:
            return
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_file.with_suffix(self.state_file.suffix + ".tmp")
            tmp.write_text(
                json.dumps({"window_start": self._window_start, "used": self._used}),
                encoding="utf-8",
            )
            os.replace(tmp, self.state_file)
        except Exception as e:
            logger.warning(f"Failed to persist limiter state {self.state_file}: {e}")

    # endregion

    def _roll_window(self, now: float) -> None:
        """Start a new window if there is none or the current one expired. Caller holds the lock."""
        if self._window_start is None or now - self._window_start >= self.window_seconds:
            self._window_start = now
            self._used = 0

    @property
    def enabled(self) -> bool:
        return self.limit > 0

    @property
    def used(self) -> int:
        with self._lock:
            self._roll_window(time.time())
            return self._used

    @property
    def remaining(self) -> int:
        if not self.enabled:
            return -1
        return max(self.limit - self.used, 0)

    @property
    def reset_at(self) -> float | None:
        """Unix timestamp when the current window ends, None if no window has started."""
        with self._lock:
            if self._window_start is None:
                return None
            return self._window_start + self.window_seconds

    def check(self, n: int = 1) -> None:
        """
        Raise DailyLimitExceeded if generating ``n`` more images would exceed the budget.
        """
        if not self.enabled:
            return
        with self._lock:
            now = time.time()
            self._roll_window(now)
            if self._used + n > self.limit:
                reset_at = self._window_start + self.window_seconds
                raise DailyLimitExceeded(
                    f"Image limit reached: {self._used}/{self.limit} used in the current window, "
                    f"resets at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(reset_at))}",
                    limit=self.limit,
                    used=self._used,
                    reset_at=reset_at,
                )

    def consume(self, n: int = 1) -> None:
        """
        Record ``n`` generated images. Call after a successful request.
        """
        if not self.enabled:
            return
        with self._lock:
            self._roll_window(time.time())
            self._used += n
            self._save()

    def reset(self) -> None:
        with self._lock:
            self._window_start, self._used = None, 0
            self._save()

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
            "window_seconds": self.window_seconds,
        }


_default_limiter: DailyImageLimiter | None = None
_default_lock = threading.Lock()


def default_state_file() -> pathlib.Path:
    env = os.environ.get(ENV_STATE_FILE)
    if env:
        return pathlib.Path(env)
    return pathlib.Path.home() / ".novelai_python" / "image_limit.json"


def get_default_limiter() -> DailyImageLimiter:
    """
    Process-wide limiter, configured from the environment:
    ``NOVELAI_DAILY_IMAGE_LIMIT`` (default 2500, 0 disables) and
    ``NOVELAI_LIMIT_STATE_FILE`` (default ~/.novelai_python/image_limit.json).
    """
    global _default_limiter
    with _default_lock:
        if _default_limiter is None:
            try:
                limit = int(os.environ.get(ENV_LIMIT, DEFAULT_IMAGE_LIMIT))
            except ValueError:
                logger.warning(f"Invalid {ENV_LIMIT}, using {DEFAULT_IMAGE_LIMIT}")
                limit = DEFAULT_IMAGE_LIMIT
            _default_limiter = DailyImageLimiter(limit, state_file=default_state_file())
        return _default_limiter


def set_default_limiter(limiter: DailyImageLimiter | None) -> None:
    global _default_limiter
    with _default_lock:
        _default_limiter = limiter
