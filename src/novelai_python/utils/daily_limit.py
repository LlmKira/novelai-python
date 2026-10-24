# @File    : daily_limit.py
"""
Local image budget: at most N images per rolling window (default 2500 / 24h).

The window is anchored at the first image generated after start-up (or after
the previous window expired), not at midnight. State is persisted to a JSON
file so the budget survives process restarts.

Off unless asked for: pass ``limiter=True`` (the process-wide limiter below) or a
``DailyImageLimiter`` to ``request()`` / ``request_stream()``. The budget is per process,
shared by every token that process uses.
"""

import json
import logging
import os
import pathlib
import tempfile
import threading
import time

from .._exceptions import DailyLimitExceeded

logger = logging.getLogger(__name__)

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
            start = data.get("window_start")
            # any valid JSON can be in the file; a window start is a number or nothing
            self._window_start = float(start) if start is not None else None
            self._used = int(data.get("used", 0))
        except Exception as e:
            logger.warning(f"Failed to read limiter state {self.state_file}: {e}, starting fresh")
            self._window_start, self._used = None, 0

    def _save(self) -> None:
        if not self.state_file:
            return
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            # a temp file of its own: another process may be saving the same state file
            fd, tmp = tempfile.mkstemp(dir=self.state_file.parent, prefix=f".{self.state_file.name}.", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"window_start": self._window_start, "used": self._used}, f)
            os.replace(tmp, self.state_file)
        except Exception as e:
            logger.warning(f"Failed to persist limiter state {self.state_file}: {e}")

    # endregion

    def _current(self, now: float) -> tuple[float | None, int]:
        """(window start, images used) at ``now``, re-read from the state file; ``(None, 0)`` when no
        window is running. Reading never starts a window, only a check or a generated image does,
        so a monitor polling the budget cannot move it. Caller holds the lock.
        """
        self._load()
        if self._window_start is None or now - self._window_start >= self.window_seconds:
            return None, 0
        return self._window_start, self._used

    def _roll_window(self, now: float) -> None:
        """Re-read the state file, then start a new window if there is none or the current one expired.

        Caller holds the lock. The file is the count: other limiters on it (in this process or
        another) may have consumed since, and a stale in-memory count would overwrite theirs.
        """
        start, used = self._current(now)
        self._window_start, self._used = (start, used) if start is not None else (now, 0)

    def _snapshot(self, now: float) -> tuple[float | None, int]:
        """One consistent (window start, used) reading, under one lock."""
        with self._lock:
            return self._current(now)

    @property
    def enabled(self) -> bool:
        return self.limit > 0

    @property
    def used(self) -> int:
        return self._snapshot(time.time())[1]

    @property
    def remaining(self) -> int:
        if not self.enabled:
            return -1
        return max(self.limit - self.used, 0)

    @property
    def reset_at(self) -> float | None:
        """Unix timestamp when the current window ends, None if no window is running."""
        start, _used = self._snapshot(time.time())
        return None if start is None else start + self.window_seconds

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
                reset_at = (self._window_start or now) + self.window_seconds
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
        start, used = self._snapshot(time.time())
        return {
            "enabled": self.enabled,
            "limit": self.limit,
            "used": used,
            "remaining": -1 if not self.enabled else max(self.limit - used, 0),
            "reset_at": None if start is None else start + self.window_seconds,
            "window_seconds": self.window_seconds,
        }


_UNSET = object()
_default_limiter: "DailyImageLimiter | object | None" = _UNSET
_default_lock = threading.Lock()


def default_state_file() -> pathlib.Path:
    env = os.environ.get(ENV_STATE_FILE)
    if env:
        return pathlib.Path(env)
    return pathlib.Path.home() / ".novelai_python" / "image_limit.json"


def get_default_limiter() -> DailyImageLimiter | None:
    """
    Process-wide limiter used by ``limiter=True``. Built on first use from the environment:
    ``NOVELAI_DAILY_IMAGE_LIMIT`` (default 2500, 0 disables) and
    ``NOVELAI_LIMIT_STATE_FILE`` (default ~/.novelai_python/image_limit.json).
    None after ``set_default_limiter(None)``.
    """
    global _default_limiter
    with _default_lock:
        if _default_limiter is _UNSET:
            try:
                limit = int(os.environ.get(ENV_LIMIT, DEFAULT_IMAGE_LIMIT))
            except ValueError:
                logger.warning(f"Invalid {ENV_LIMIT}, using {DEFAULT_IMAGE_LIMIT}")
                limit = DEFAULT_IMAGE_LIMIT
            _default_limiter = DailyImageLimiter(limit, state_file=default_state_file())
        return _default_limiter if isinstance(_default_limiter, DailyImageLimiter) else None


def set_default_limiter(limiter: DailyImageLimiter | None) -> None:
    """Replace the process-wide limiter; None turns ``limiter=True`` into no limit."""
    global _default_limiter
    with _default_lock:
        _default_limiter = limiter
