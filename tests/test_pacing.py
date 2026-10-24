"""The pacer waits AFTER a request, never before the first one; tests use a fake clock."""

import io
import random
import zipfile
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import GenerateImageInfer, RequestPacer, get_default_pacer, set_default_pacer
from novelai_python.utils import pacing


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    """Monotonic time the pacer sees; asyncio.sleep inside the pacer advances it instead of waiting."""
    fake = FakeClock()

    async def sleep(seconds):
        fake.now += seconds

    monkeypatch.setattr(pacing.asyncio, "sleep", sleep)
    return fake


def test_gap_starts_when_the_request_ends(clock):
    pacer = RequestPacer(2, 4, clock=clock, rng=random.Random(1))
    assert pacer.remaining() == 0  # the first request never waits
    pacer.done()
    gap = pacer.remaining()
    assert 2 <= gap <= 4
    clock.now += gap + 10  # a long pause: the next request goes out at once
    assert pacer.remaining() == 0


def test_bad_gaps_are_rejected():
    with pytest.raises(ValueError):
        RequestPacer(5, 1)
    with pytest.raises(ValueError):
        RequestPacer(-1, 1)
    assert RequestPacer(0, 0).enabled is False


@pytest.mark.asyncio
async def test_slot_waits_only_for_the_remainder(clock):
    pacer = RequestPacer(3, 3, clock=clock)  # a fixed 3 s gap
    async with pacer.slot() as waited:
        assert waited == 0
        clock.now += 5  # the request itself took 5 s
    started = clock.now
    clock.now += 1  # the caller did something else for 1 s of the 3 s gap
    async with pacer.slot() as waited:
        assert waited == pytest.approx(2)
        assert clock.now == pytest.approx(started + 3)
    assert pacer.waits == 2
    assert pacer.waited_total == pytest.approx(2)
    assert pacer.status()["waits"] == 2


@pytest.mark.asyncio
async def test_disabled_pacer_never_waits(clock):
    pacer = RequestPacer(0, 0, clock=clock)
    for _ in range(3):
        async with pacer.slot() as waited:
            assert waited == 0
    assert pacer.waits == 0
    assert clock.now == 1000.0


@pytest.mark.asyncio
async def test_slot_restarts_the_gap_even_when_the_request_fails(clock):
    pacer = RequestPacer(2, 2, clock=clock)
    with pytest.raises(RuntimeError):
        async with pacer.slot():
            raise RuntimeError("boom")
    assert pacer.remaining() == pytest.approx(2)


def test_gap_from_env(monkeypatch):
    monkeypatch.setenv(pacing.ENV_GAP, "2,5")
    assert pacing._gap_from_env() == (2.0, 5.0)
    monkeypatch.setenv(pacing.ENV_GAP, "0")
    assert pacing._gap_from_env() == (0.0, 0.0)
    monkeypatch.setenv(pacing.ENV_GAP, "3")
    assert pacing._gap_from_env() == (3.0, 3.0)
    monkeypatch.setenv(pacing.ENV_GAP, "fast")
    assert pacing._gap_from_env() == (pacing.DEFAULT_MIN_GAP, pacing.DEFAULT_MAX_GAP)
    monkeypatch.delenv(pacing.ENV_GAP)
    assert pacing._gap_from_env() == (pacing.DEFAULT_MIN_GAP, pacing.DEFAULT_MAX_GAP)


def test_default_pacer_resolution():
    own = RequestPacer(1, 2)
    set_default_pacer(None)
    try:
        default = get_default_pacer()
        assert get_default_pacer() is default
        assert pacing.resolve_pacer(True) is default
        assert pacing.resolve_pacer(own) is own
        assert pacing.resolve_pacer(None) is None
        assert pacing.resolve_pacer(False) is None
    finally:
        set_default_pacer(None)


@pytest.mark.asyncio
async def test_request_with_pacer_starts_the_gap_after_the_response(clock, monkeypatch):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("image_0.webp", b"RIFF....WEBP")
    response = mock.Mock()
    response.status_code = 200
    response.headers = {"Content-Type": "binary/octet-stream"}
    response.content = buf.getvalue()

    pacer = RequestPacer(4, 4, clock=clock)

    async def post(*args, **kwargs):
        assert pacer.remaining() == 0  # nothing waited before the request
        clock.now += 7  # NovelAI took 7 s
        return response

    session = AsyncSession()
    monkeypatch.setattr(session, "post", post)
    gen = GenerateImageInfer.build_generate("1girl")
    await gen.request(session, pacer=pacer)
    assert pacer.remaining() == pytest.approx(4)  # the gap counts from the response, not the start
    await gen.request(session, pacer=pacer)  # the second request waited the 4 s on the fake clock
    assert pacer.waits == 2
    assert pacer.waited_total == pytest.approx(4)
    clock.now += 10  # gap over; a request without a pacer neither waits nor restarts the gap
    await gen.request(session, pacer=None)
    assert pacer.waits == 2
    assert pacer.remaining() == 0
    await session.close()
