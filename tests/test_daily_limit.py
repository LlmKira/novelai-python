import json
import time

import pytest

from novelai_python import DailyLimitExceeded
from novelai_python.utils.daily_limit import DailyImageLimiter


def test_limit_blocks_after_budget(tmp_path):
    limiter = DailyImageLimiter(3, state_file=tmp_path / "state.json")
    limiter.check(2)
    limiter.consume(2)
    assert limiter.used == 2
    assert limiter.remaining == 1
    limiter.check(1)
    with pytest.raises(DailyLimitExceeded) as e:
        limiter.check(2)
    assert e.value.limit == 3
    assert e.value.used == 2
    assert e.value.reset_at > time.time()


def test_state_persists_across_instances(tmp_path):
    state = tmp_path / "state.json"
    DailyImageLimiter(10, state_file=state).consume(4)
    again = DailyImageLimiter(10, state_file=state)
    assert again.used == 4
    assert json.loads(state.read_text())["used"] == 4


def test_limiters_sharing_a_file_add_up(tmp_path):
    state = tmp_path / "s.json"
    a = DailyImageLimiter(10, state_file=state)
    b = DailyImageLimiter(10, state_file=state)
    a.consume(9)
    b.consume(1)
    assert DailyImageLimiter(10, state_file=state).used == 10
    with pytest.raises(DailyLimitExceeded):
        a.check(1)


def test_window_rolls_over_from_first_use(tmp_path):
    state = tmp_path / "state.json"
    limiter = DailyImageLimiter(1, window_seconds=60, state_file=state)
    limiter.consume(1)
    with pytest.raises(DailyLimitExceeded):
        limiter.check(1)
    # pretend the window started long ago
    data = json.loads(state.read_text())
    data["window_start"] = time.time() - 120
    state.write_text(json.dumps(data))
    fresh = DailyImageLimiter(1, window_seconds=60, state_file=state)
    fresh.check(1)
    assert fresh.used == 0


def test_disabled_limiter_never_blocks():
    limiter = DailyImageLimiter(0)
    limiter.check(10_000)
    limiter.consume(10_000)
    assert limiter.remaining == -1
    assert limiter.enabled is False


def test_default_limiter_reads_env(monkeypatch, tmp_path):
    from novelai_python.utils import daily_limit

    monkeypatch.setenv(daily_limit.ENV_LIMIT, "7")
    monkeypatch.setenv(daily_limit.ENV_STATE_FILE, str(tmp_path / "env_state.json"))
    monkeypatch.setattr(daily_limit, "_default_limiter", daily_limit._UNSET)
    limiter = daily_limit.get_default_limiter()
    assert limiter is not None
    assert limiter.limit == 7
    assert limiter.state_file == tmp_path / "env_state.json"


def test_set_default_limiter_none_disables_it(monkeypatch):
    from novelai_python.utils import daily_limit

    monkeypatch.setattr(daily_limit, "_default_limiter", daily_limit._UNSET)
    daily_limit.set_default_limiter(None)
    assert daily_limit.get_default_limiter() is None


def test_state_file_with_a_string_window_start(tmp_path):
    state = tmp_path / "state.json"
    state.write_text('{"window_start": "nonsense", "used": 3}', encoding="utf-8")
    limiter = DailyImageLimiter(5, state_file=state)
    limiter.check(1)
    assert limiter.status()["used"] == 0  # unreadable state starts fresh
    state.write_text('{"window_start": "1792000000.5", "used": "2"}', encoding="utf-8")
    assert DailyImageLimiter(5, state_file=state)._window_start == 1792000000.5


def test_reading_the_budget_never_starts_or_moves_a_window():
    limiter = DailyImageLimiter(5, window_seconds=60)  # in memory: nothing re-reads a file
    assert (limiter.remaining, limiter.used, limiter.reset_at) == (5, 0, None)
    assert limiter.status()["reset_at"] is None  # a monitor polled it: still no window
    limiter.consume(2)
    started = limiter.reset_at
    assert started is not None and limiter.remaining == 3

    # the window expired: reads see a fresh budget but do not anchor a new window
    limiter._window_start -= 120
    assert (limiter.remaining, limiter.reset_at) == (5, None)
    time.sleep(0.01)
    limiter.consume(1)  # the next image starts the next window
    assert limiter.reset_at > started and limiter.remaining == 4
