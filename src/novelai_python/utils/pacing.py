"""A human-like gap between requests, measured from the end of the previous one.

NovelAI answers 429 "Concurrent generation is locked" when a request lands right after the
last one. A pacer keeps a random gap between requests, but counts it from the moment the previous
request finished: the first request of a quiet account goes out at once, a request that arrives
after a long pause goes out at once, and only a request that follows another one closely waits
for the remainder of the gap. Requests through one pacer are serialized, like one account can
only generate one image at a time.

Off unless asked for: pass ``pacer=True`` (the process-wide pacer, ``NOVELAI_REQUEST_GAP``,
default ``1,10`` seconds) or a ``RequestPacer`` to ``request()`` / ``request_stream()``, or use
``async with pacer.slot(): ...`` around any request.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import threading
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

ENV_GAP = "NOVELAI_REQUEST_GAP"
"""``min,max`` seconds of the process-wide pacer; ``0`` disables it."""
DEFAULT_MIN_GAP = 1.0
DEFAULT_MAX_GAP = 10.0


class RequestPacer:
    def __init__(
        self,
        min_gap: float = DEFAULT_MIN_GAP,
        max_gap: float = DEFAULT_MAX_GAP,
        *,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
    ) -> None:
        """
        :param min_gap: shortest gap after a request, seconds
        :param max_gap: longest gap after a request, seconds; 0 for both disables the pacer
        :param clock: monotonic clock, replaceable in tests
        :param rng: random source, replaceable in tests
        """
        if min_gap < 0 or max_gap < min_gap:
            raise ValueError("need 0 <= min_gap <= max_gap")
        self.min_gap, self.max_gap = float(min_gap), float(max_gap)
        self._clock = clock
        self._rng = rng or random.Random()
        self._next_at: float = 0.0  # earliest moment the next request may start
        self._lock: asyncio.Lock | None = None
        self._lock_loop: asyncio.AbstractEventLoop | None = None
        self.waited_total = 0.0
        self.waits = 0

    @property
    def enabled(self) -> bool:
        return self.max_gap > 0

    def _get_lock(self) -> asyncio.Lock:
        # an asyncio.Lock belongs to one event loop; a pacer can outlive it (several asyncio.run)
        loop = asyncio.get_running_loop()
        if self._lock is None or self._lock_loop is not loop:
            self._lock, self._lock_loop = asyncio.Lock(), loop
        return self._lock

    def remaining(self) -> float:
        """Seconds until the next request may start; 0 when it may start now."""
        return max(0.0, self._next_at - self._clock())

    def done(self) -> None:
        """The request finished: the next one may start after a fresh random gap."""
        if self.enabled:
            self._next_at = self._clock() + self._rng.uniform(self.min_gap, self.max_gap)

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[float]:
        """Wait for the gap, run the request, then start the next gap. Yields the seconds waited."""
        if not self.enabled:
            yield 0.0
            return
        async with self._get_lock():
            wait = self.remaining()
            if wait > 0:
                logger.debug(f"pacing: waiting {wait:.1f}s after the previous request")
                await asyncio.sleep(wait)
            self.waits += 1
            self.waited_total += wait
            try:
                from ..metrics import get_metrics

                get_metrics().observe_pacing_wait(wait)
            except Exception:  # metrics are optional
                pass
            try:
                yield wait
            finally:
                self.done()

    def status(self) -> dict:
        return {
            "min_gap": self.min_gap,
            "max_gap": self.max_gap,
            "next_in": round(self.remaining(), 3),
            "waits": self.waits,
            "waited_total": round(self.waited_total, 3),
        }


_default: RequestPacer | None = None
_default_lock = threading.Lock()


def _gap_from_env() -> tuple[float, float]:
    raw = os.environ.get(ENV_GAP)
    if not raw:
        return DEFAULT_MIN_GAP, DEFAULT_MAX_GAP
    try:
        parts = [float(x) for x in raw.split(",")]
    except ValueError:
        logger.warning(f"{ENV_GAP}={raw!r} is not 'min,max'; using the defaults")
        return DEFAULT_MIN_GAP, DEFAULT_MAX_GAP
    if len(parts) == 1:
        return (0.0, 0.0) if parts[0] <= 0 else (parts[0], parts[0])
    return parts[0], parts[1]


def get_default_pacer() -> RequestPacer:
    """The process-wide pacer (``NOVELAI_REQUEST_GAP``), created on first use."""
    global _default
    with _default_lock:
        if _default is None:
            _default = RequestPacer(*_gap_from_env())
        return _default


def set_default_pacer(pacer: RequestPacer | None) -> None:
    global _default
    with _default_lock:
        _default = pacer


def resolve_pacer(pacer: RequestPacer | bool | None) -> RequestPacer | None:
    """``True`` -> the default pacer, a pacer -> itself, ``None``/``False`` -> no pacing."""
    if pacer is True:
        return get_default_pacer()
    if isinstance(pacer, RequestPacer):
        return pacer
    return None


@asynccontextmanager
async def paced(pacer: RequestPacer | bool | None) -> AsyncIterator[float]:
    """``async with paced(pacer):`` around a request; a no-op when ``pacer`` resolves to None."""
    resolved = resolve_pacer(pacer)
    if resolved is None:
        yield 0.0
        return
    async with resolved.slot() as waited:
        yield waited


__all__ = [
    "DEFAULT_MAX_GAP",
    "DEFAULT_MIN_GAP",
    "ENV_GAP",
    "RequestPacer",
    "get_default_pacer",
    "paced",
    "resolve_pacer",
    "set_default_pacer",
]
