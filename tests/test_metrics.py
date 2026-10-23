"""Metrics are optional and offline: every test here runs against its own CollectorRegistry."""

import asyncio
import io
import json
import urllib.request
import zipfile
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession
from prometheus_client import CollectorRegistry

from novelai_python import GenerateImageInfer, Subscription, SubscriptionResp, _retry
from novelai_python.credential import ApiCredential, LoginCredential, SecretStr
from novelai_python.metrics import (
    STATUS_TRANSPORT,
    NovelAIMetrics,
    account_label,
    endpoint_label,
    get_metrics,
    model_label,
    set_metrics,
    short_hash,
)

SUBSCRIPTION = {
    "tier": 3,
    "active": True,
    "expiresAt": 1708646400,
    "perks": {
        "maxPriorityActions": 1000,
        "startPriority": 10,
        "moduleTrainingSteps": 10000,
        "unlimitedMaxPriority": True,
        "voiceGeneration": True,
        "imageGeneration": True,
        "contextTokens": 8192,
    },
    "paymentProcessorData": None,
    "trainingStepsLeft": {"fixedTrainingStepsLeft": 8825, "purchasedTrainingSteps": 150},
    "accountType": 0,
    "usage": {"percent": 42, "purchasedPercent": 0, "isNegative": False, "timeUntilNextPercent": 864},
}


@pytest.fixture
def metrics():
    """A fresh registry installed as the process-wide metrics for one test."""
    previous = get_metrics()
    fresh = NovelAIMetrics(registry=CollectorRegistry())
    set_metrics(fresh)
    try:
        yield fresh
    finally:
        set_metrics(previous)


def _value(metrics: NovelAIMetrics, name: str, **labels):
    return metrics.registry.get_sample_value(name, labels or None)


def _response(status: int, content: bytes, content_type: str = "application/json"):
    response = mock.Mock()
    response.status_code = status
    response.headers = {"Content-Type": content_type}
    response.content = content
    response.json = lambda: json.loads(content)
    return response


def _mock_session(response):
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=response)
    session.post = mock.AsyncMock(return_value=response)
    session.request = session.get
    session.headers = {}
    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)
    return session


# region labels


def test_labels_are_bounded():
    assert endpoint_label("https://image.novelai.net/ai/generate-image?x=1") == "/ai/generate-image"
    assert endpoint_label("https://api.novelai.net/") == "/"
    assert model_label(None) == ""
    assert model_label("nai-diffusion-5-full") == "nai-diffusion-5-full"
    assert model_label(GenerateImageInfer.build_generate("1girl").model) == "nai-diffusion-5-full"
    assert len(short_hash("user@example.com")) == 8
    assert short_hash("a") != short_hash("b")


def test_account_label_never_exposes_the_email():
    cred = LoginCredential(username="user@example.com", password=SecretStr("secret"))
    label = account_label(cred)
    assert label == short_hash("user@example.com")
    assert "example" not in label
    assert account_label(ApiCredential(api_token=SecretStr("pst-abc"))) == short_hash("pst-abc")
    cred.metrics_label = "main"
    assert account_label(cred) == "main"
    assert account_label(mock.MagicMock(spec=AsyncSession)) == "session"


# endregion


# region observing


def test_observe_counts_status_and_duration(metrics):
    with metrics.observe("https://image.novelai.net/ai/generate-image", "nai-diffusion-5-full") as obs:
        obs.ok(200)
    labels = {"endpoint": "/ai/generate-image", "model": "nai-diffusion-5-full"}
    assert _value(metrics, "novelai_requests_total", status="200", **labels) == 1
    assert _value(metrics, "novelai_request_seconds_count", **labels) == 1
    assert _value(metrics, "novelai_inflight_requests", endpoint="/ai/generate-image") == 0
    assert _value(metrics, "novelai_last_success_timestamp_seconds", endpoint="/ai/generate-image") > 0


def test_observe_failed_and_transport(metrics):
    with metrics.observe("https://api.novelai.net/user/subscription") as obs:
        obs.failed(401)
    with pytest.raises(RuntimeError), metrics.observe("https://api.novelai.net/user/subscription"):
        raise RuntimeError("ssl")
    labels = {"endpoint": "/user/subscription", "model": ""}
    assert _value(metrics, "novelai_requests_total", status="401", **labels) == 1
    assert _value(metrics, "novelai_requests_total", status=STATUS_TRANSPORT, **labels) == 1
    assert _value(metrics, "novelai_last_success_timestamp_seconds", endpoint="/user/subscription") is None


def test_observe_subscription_fills_the_account_gauges(metrics):
    resp = SubscriptionResp.model_validate(SUBSCRIPTION)
    metrics.observe_subscription(resp, "main")
    assert _value(metrics, "novelai_anlas_available", account="main") == 8975
    assert _value(metrics, "novelai_anlas_fixed", account="main") == 8825
    assert _value(metrics, "novelai_anlas_purchased", account="main") == 150
    assert _value(metrics, "novelai_subscription_tier", account="main") == 3
    assert _value(metrics, "novelai_subscription_active", account="main") == 1
    assert _value(metrics, "novelai_subscription_expires_timestamp_seconds", account="main") == 1708646400
    assert _value(metrics, "novelai_opus_usage_percent", account="main") == 42
    assert _value(metrics, "novelai_opus_usage_negative", account="main") == 0
    assert _value(metrics, "novelai_opus_usage_refill_percent_per_day", account="main") == 100
    assert _value(metrics, "novelai_opus_images_left", account="main") == int(42 * 17.3)
    assert _value(metrics, "novelai_account_updated_timestamp_seconds", account="main") > 0
    metrics.observe_subscription(None, "main")  # non-Opus /user/data: nothing to record, no error


@pytest.mark.asyncio
async def test_subscription_request_is_observed_end_to_end(metrics):
    session = _mock_session(_response(200, json.dumps(SUBSCRIPTION).encode()))
    await Subscription().request(session)
    assert _value(metrics, "novelai_requests_total", endpoint="/user/subscription", model="", status="200") == 1
    assert _value(metrics, "novelai_anlas_available", account="session") == 8975


@pytest.mark.asyncio
async def test_image_request_counts_images_and_retries(metrics, monkeypatch):
    slept = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(_retry.asyncio, "sleep", fake_sleep)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("image_0.webp", b"RIFF....WEBP")
        zf.writestr("image_1.webp", b"RIFF....WEBP")
    error = _response(500, b'{"statusCode": 500, "message": "Error generating image"}')
    ok = _response(200, buf.getvalue(), "binary/octet-stream")
    session = AsyncSession()
    monkeypatch.setattr(session, "post", mock.AsyncMock(side_effect=[error, ok]))
    resp = await GenerateImageInfer.build_generate("1girl").request(session)
    await session.close()
    assert len(resp.files or []) == 2
    labels = {"endpoint": "/ai/generate-image", "model": "nai-diffusion-5-full"}
    assert _value(metrics, "novelai_requests_total", status="500", **labels) == 1
    assert _value(metrics, "novelai_requests_total", status="200", **labels) == 1
    assert _value(metrics, "novelai_images_total", model="nai-diffusion-5-full") == 2
    assert _value(metrics, "novelai_retries_total", endpoint="/ai/generate-image") == 1
    assert _value(metrics, "novelai_retry_wait_seconds_count") == 1
    assert slept and 1.0 <= slept[0] <= 3.0


def test_retry_backoff_grows_and_is_jittered(monkeypatch):
    waits = []
    calls = []

    async def fake_sleep(seconds):
        waits.append(seconds)

    monkeypatch.setattr(_retry.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(_retry.random, "uniform", lambda a, b: (a + b) / 2)

    class Boom(Exception):
        code = 500

    @_retry.retry_on_server_error(attempts=4, min_wait=1.0, max_wait=3.0, backoff=2.0)
    async def flaky():
        calls.append(1)
        raise Boom()

    with pytest.raises(Boom):
        asyncio.run(flaky())
    assert len(calls) == 4
    assert waits == [2.0, 4.0, 8.0]  # uniform(1, 3) = 2, doubled per retry


# endregion


# region exposing


def test_generate_latest_and_info(metrics):
    text = metrics.generate_latest().decode()
    assert "novelai_sdk_info" in text
    assert "impersonate=" in text
    assert metrics.content_type.startswith("text/plain")


def test_disabled_by_env(monkeypatch):
    monkeypatch.setenv("NOVELAI_METRICS", "0")
    off = NovelAIMetrics(registry=CollectorRegistry())
    assert off.enabled is False
    with off.observe("https://api.novelai.net/user/subscription") as obs:
        obs.ok()
    off.observe_subscription(SubscriptionResp.model_validate(SUBSCRIPTION), "x")
    assert off.generate_latest() == b""
    with pytest.raises(RuntimeError):
        off.asgi_app()


def test_push_to_victoriametrics_builds_the_import_request(metrics, monkeypatch):
    seen = {}

    class _Response:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class _Opener:
        def open(self, request, timeout):
            seen["url"] = request.full_url
            seen["method"] = request.get_method()
            seen["body"] = request.data
            seen["timeout"] = timeout
            return _Response()

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: _Opener())
    metrics.push_to_victoriametrics("http://vm:8428/", extra_labels={"job": "nai sdk", "instance": "a"}, timeout=3)
    assert seen["url"] == "http://vm:8428/api/v1/import/prometheus?extra_label=job=nai%20sdk&extra_label=instance=a"
    assert seen["method"] == "POST"
    assert b"novelai_sdk_info" in seen["body"]
    assert seen["timeout"] == 3


def test_server_metrics_endpoint(metrics, monkeypatch):
    from fastapi.testclient import TestClient

    from novelai_python.server import app

    client = TestClient(app)
    monkeypatch.delenv("NOVELAI_METRICS_TOKEN", raising=False)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "novelai_sdk_info" in response.text

    monkeypatch.setenv("NOVELAI_METRICS_TOKEN", "s3cret")
    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer s3cret"}).status_code == 200


# endregion
