"""Metrics are optional and offline: every test here runs against a NovelAIMetrics of its own."""

import asyncio
import gzip
import io
import json
import logging
import urllib.request
import zipfile
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession
from curl_cffi.requests.errors import RequestsError
from prometheus_client import CollectorRegistry, generate_latest

from novelai_python import (
    AuthError,
    GenerateImageInfer,
    OAIChatCompletion,
    OAIChatMessage,
    SessionHttpError,
    Subscription,
    SubscriptionResp,
    SuggestTags,
    _retry,
)
from novelai_python.credential import ApiCredential, CredentialBase, LoginCredential, SecretStr
from novelai_python.metrics import (
    STATUS_TRANSPORT,
    TRANSPORT_STATUSES,
    NovelAIMetrics,
    account_label,
    endpoint_label,
    get_metrics,
    model_label,
    set_metrics,
    short_hash,
    transport_label,
)
from novelai_python.utils.daily_limit import DailyImageLimiter

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
GENERATE = {"endpoint": "/ai/generate-image", "model": "nai-diffusion-5-full"}


@pytest.fixture
def metrics():
    """Fresh metrics installed as the process-wide ones for one test."""
    previous = get_metrics()
    fresh = NovelAIMetrics()
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
    response.aclose = mock.AsyncMock()
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


def _wrapped_curl_error(code: int, message: str = "curl failed") -> SessionHttpError:
    """A curl error the way the SDK raises it: wrapped in SessionHttpError."""
    try:
        try:
            raise RequestsError(message, code=code)
        except RequestsError as exc:
            raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.") from exc
    except SessionHttpError as outer:
        return outer


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


def test_transport_failures_are_classified_by_curl_code():
    assert transport_label(RequestsError("t", code=28)) == "timeout"
    assert transport_label(_wrapped_curl_error(28)) == "timeout"
    assert transport_label(_wrapped_curl_error(6)) == "dns"
    assert transport_label(_wrapped_curl_error(5)) == "proxy"
    assert transport_label(_wrapped_curl_error(97)) == "proxy"
    assert transport_label(_wrapped_curl_error(56, "CONNECT tunnel failed, response 407")) == "proxy"
    assert transport_label(_wrapped_curl_error(7)) == "connect"
    assert transport_label(_wrapped_curl_error(60)) == "ssl"
    assert transport_label(_wrapped_curl_error(35)) == "ssl"
    assert transport_label(_wrapped_curl_error(56)) == "reset"
    assert transport_label(_wrapped_curl_error(99)) == STATUS_TRANSPORT
    assert transport_label(asyncio.CancelledError()) == "cancelled"
    assert transport_label(TimeoutError()) == "timeout"
    # not a transport failure: no request went out, nothing to count
    assert transport_label(RuntimeError("bug")) is None
    assert transport_label(None) is None
    assert set(TRANSPORT_STATUSES) == {"timeout", "dns", "proxy", "connect", "ssl", "reset", "cancelled", "transport"}


# endregion


# region observing


def test_observe_counts_status_and_duration(metrics):
    with metrics.observe("https://image.novelai.net/ai/generate-image", "nai-diffusion-5-full") as obs:
        obs.report(200)
    assert _value(metrics, "novelai_requests_total", status="200", **GENERATE) == 1
    assert _value(metrics, "novelai_request_duration_seconds_count", **GENERATE) == 1
    assert _value(metrics, "novelai_requests_in_flight", endpoint="/ai/generate-image") == 0
    assert _value(metrics, "novelai_last_success_timestamp_seconds", endpoint="/ai/generate-image") > 0


def test_observe_failures(metrics):
    with metrics.observe("https://api.novelai.net/user/subscription") as obs:
        obs.report(401)
    with pytest.raises(SessionHttpError), metrics.observe("https://image.novelai.net/ai/generate-image", "m"):
        raise _wrapped_curl_error(28)
    with pytest.raises(asyncio.CancelledError), metrics.observe("https://image.novelai.net/ai/generate-image", "m"):
        raise asyncio.CancelledError()
    assert _value(metrics, "novelai_requests_total", endpoint="/user/subscription", model="", status="401") == 1
    assert _value(metrics, "novelai_requests_total", endpoint="/ai/generate-image", model="m", status="timeout") == 1
    assert _value(metrics, "novelai_requests_total", endpoint="/ai/generate-image", model="m", status="cancelled") == 1
    assert _value(metrics, "novelai_last_success_timestamp_seconds", endpoint="/user/subscription") is None


def test_a_failure_before_the_request_is_not_counted(metrics):
    with pytest.raises(ValueError), metrics.observe("https://image.novelai.net/ai/generate-image", "m"):
        raise ValueError("bad parameters")
    assert (
        _value(metrics, "novelai_requests_total", endpoint="/ai/generate-image", model="m", status="transport") is None
    )
    assert _value(metrics, "novelai_request_duration_seconds_count", endpoint="/ai/generate-image", model="m") is None
    assert _value(metrics, "novelai_requests_in_flight", endpoint="/ai/generate-image") == 0


@pytest.mark.asyncio
async def test_a_failed_login_is_not_a_generate_request(metrics):
    class FailingCredential(CredentialBase):
        async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
            raise AuthError("login failed", request={}, response={}, code=401)

    with pytest.raises(AuthError):
        await GenerateImageInfer.build_generate("1girl").request(FailingCredential())
    assert "novelai_requests_total{" not in metrics.generate_latest().decode()


def test_observe_subscription_fills_the_account_gauges(metrics):
    metrics.observe_subscription(SubscriptionResp.model_validate(SUBSCRIPTION), "main")
    assert _value(metrics, "novelai_account_anlas", account="main", kind="fixed") == 8825
    assert _value(metrics, "novelai_account_anlas", account="main", kind="purchased") == 150
    assert _value(metrics, "novelai_subscription_tier", account="main") == 3
    assert _value(metrics, "novelai_subscription_active", account="main") == 1
    assert _value(metrics, "novelai_subscription_expires_timestamp_seconds", account="main") == 1708646400
    assert _value(metrics, "novelai_opus_usage_ratio", account="main") == pytest.approx(0.42)
    assert _value(metrics, "novelai_opus_usage_negative", account="main") == 0
    assert _value(metrics, "novelai_opus_usage_refill_ratio_per_second", account="main") == pytest.approx(0.01 / 864)
    assert _value(metrics, "novelai_opus_images_left", account="main") == int(42 * 17.3)
    assert _value(metrics, "novelai_account_updated_timestamp_seconds", account="main") > 0
    metrics.observe_subscription(None, "main")  # /user/data without a subscription: nothing to record


def test_the_usage_bar_goes_away_with_opus(metrics):
    metrics.observe_subscription(SubscriptionResp.model_validate(SUBSCRIPTION), "main")
    without_usage = {k: v for k, v in SUBSCRIPTION.items() if k != "usage"} | {"tier": 1}
    metrics.observe_subscription(SubscriptionResp.model_validate(without_usage), "main")
    assert _value(metrics, "novelai_opus_usage_ratio", account="main") is None
    assert _value(metrics, "novelai_opus_images_left", account="main") is None
    assert _value(metrics, "novelai_subscription_tier", account="main") == 1
    assert _value(metrics, "novelai_account_anlas", account="main", kind="fixed") == 8825


def test_account_gauges_are_capped(caplog):
    capped = NovelAIMetrics(max_accounts=2)
    resp = SubscriptionResp.model_validate(SUBSCRIPTION)
    with caplog.at_level(logging.WARNING, logger="novelai_python.metrics"):
        for account in ("a", "b", "c", "d", "a"):
            capped.observe_subscription(resp, account)
    assert _value(capped, "novelai_subscription_tier", account="a") == 3
    assert _value(capped, "novelai_subscription_tier", account="b") == 3
    assert _value(capped, "novelai_subscription_tier", account="c") is None
    assert _value(capped, "novelai_subscription_tier", account="d") is None
    assert sum("account gauges skip" in r.getMessage() for r in caplog.records) == 1


def test_the_limit_gauge_is_read_at_scrape_time(metrics):
    assert _value(metrics, "novelai_local_limit_remaining_images") == -1  # no limiter used yet
    limiter = DailyImageLimiter(3)
    limiter.consume(1)
    metrics.observe_limiter(limiter)
    assert _value(metrics, "novelai_local_limit_remaining_images") == 2
    limiter.consume(2)  # no observe_limiter: the gauge reads the limiter when scraped
    assert _value(metrics, "novelai_local_limit_remaining_images") == 0
    metrics.observe_limiter(DailyImageLimiter(0))
    assert _value(metrics, "novelai_local_limit_remaining_images") == -1  # a disabled limiter


@pytest.mark.asyncio
async def test_subscription_request_is_observed_end_to_end(metrics):
    session = _mock_session(_response(200, json.dumps(SUBSCRIPTION).encode()))
    await Subscription().request(session)
    assert _value(metrics, "novelai_requests_total", endpoint="/user/subscription", model="", status="200") == 1
    assert _value(metrics, "novelai_account_anlas", account="session", kind="fixed") == 8825


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
    assert _value(metrics, "novelai_requests_total", status="500", **GENERATE) == 1
    assert _value(metrics, "novelai_requests_total", status="200", **GENERATE) == 1
    assert _value(metrics, "novelai_images_total", model="nai-diffusion-5-full") == 2
    assert _value(metrics, "novelai_retries_total", endpoint="/ai/generate-image") == 1
    assert _value(metrics, "novelai_retry_wait_seconds_count") == 1
    assert slept and 1.0 <= slept[0] <= 3.0


@pytest.mark.asyncio
async def test_suggest_tags_and_the_openai_stream_are_observed(metrics):
    tags = _mock_session(_response(200, b'{"tags": [{"tag": "1girl", "count": 5, "confidence": 0.9}]}'))
    await SuggestTags(prompt="1gi").request(tags)
    assert (
        _value(
            metrics,
            "novelai_requests_total",
            endpoint="/ai/generate-image/suggest-tags",
            model="nai-diffusion-4-5-full",
            status="200",
        )
        == 1
    )

    async def aiter_lines():
        for line in (b'data: {"choices":[{"delta":{"content":"hi"}}]}', b"data: [DONE]"):
            yield line

    stream = _response(200, b"", "text/event-stream")
    stream.aiter_lines = aiter_lines
    chat = OAIChatCompletion(model="glm-4-6", messages=[OAIChatMessage(role="user", content="hi")])
    assert [c async for c in chat.stream(_mock_session(stream))]
    labels = {"endpoint": "/oa/v1/chat/completions", "model": "glm-4-6"}
    assert _value(metrics, "novelai_requests_total", status="200", **labels) == 1


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


# region registry and exposition


def test_created_series_are_left_out(metrics):
    with metrics.observe("https://api.novelai.net/user/subscription") as obs:
        obs.report(200)
    text = metrics.generate_latest().decode()
    assert "novelai_requests_total" in text
    assert "_created" not in text
    keep = NovelAIMetrics(created_series=True)
    with keep.observe("https://api.novelai.net/user/subscription") as obs:
        obs.report(200)
    assert "novelai_requests_created" in keep.generate_latest().decode()


def test_metrics_can_join_the_callers_registry():
    registry = CollectorRegistry()
    joined = NovelAIMetrics(registry=registry)
    with joined.observe("https://api.novelai.net/user/subscription") as obs:
        obs.report(200)
    assert registry.get_sample_value(
        "novelai_requests_total", {"endpoint": "/user/subscription", "model": "", "status": "200"}
    )
    assert "python_info" not in generate_latest(registry).decode()  # process metrics only on request


def test_process_metrics_are_opt_in():
    assert "python_info" not in NovelAIMetrics().generate_latest().decode()
    assert "python_info" in NovelAIMetrics(process_metrics=True).generate_latest().decode()


def test_generate_latest_and_info(metrics):
    text = metrics.generate_latest().decode()
    assert "novelai_sdk_info" in text
    assert "impersonate=" in text
    assert metrics.content_type.startswith("text/plain")


def test_disabled_by_env(monkeypatch):
    monkeypatch.setenv("NOVELAI_METRICS", "0")
    off = NovelAIMetrics()
    assert off.enabled is False
    with off.observe("https://api.novelai.net/user/subscription") as obs:
        obs.report(200)
    off.observe_subscription(SubscriptionResp.model_validate(SUBSCRIPTION), "x")
    off.observe_limiter(DailyImageLimiter(3))
    assert off.generate_latest() == b""
    with pytest.raises(RuntimeError):
        off.asgi_app()


def _capture_push(monkeypatch):
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
            seen["encoding"] = request.get_header("Content-encoding")
            seen["timeout"] = timeout
            return _Response()

    monkeypatch.setattr(urllib.request, "build_opener", lambda *handlers: _Opener())
    return seen


def test_push_to_victoriametrics_builds_the_import_request(metrics, monkeypatch):
    seen = _capture_push(monkeypatch)
    metrics.push_to_victoriametrics("http://vm:8428/", extra_labels={"job": "nai sdk", "instance": "a"}, timeout=3)
    assert seen["url"] == "http://vm:8428/api/v1/import/prometheus?extra_label=job=nai%20sdk&extra_label=instance=a"
    assert seen["method"] == "POST"
    assert seen["encoding"] == "gzip"
    assert b"novelai_sdk_info" in gzip.decompress(seen["body"])
    assert seen["timeout"] == 3

    seen = _capture_push(monkeypatch)
    metrics.push_to_victoriametrics("http://vm:8428", compress=False)
    assert seen["encoding"] is None
    assert b"novelai_sdk_info" in seen["body"]


def test_asgi_app_serves_add_route_and_mount(metrics):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    routed = FastAPI()
    routed.add_route("/metrics", metrics.asgi_app())  # a plain function fails here on client_python 0.26
    response = TestClient(routed).get("/metrics", follow_redirects=False)
    assert response.status_code == 200
    assert "novelai_sdk_info" in response.text

    mounted = FastAPI()
    mounted.mount("/metrics", metrics.asgi_app())
    assert "novelai_sdk_info" in TestClient(mounted).get("/metrics/").text


def test_server_metrics_endpoint(metrics, monkeypatch):
    from fastapi.testclient import TestClient

    from novelai_python.server import app

    client = TestClient(app)
    monkeypatch.delenv("NOVELAI_METRICS_TOKEN", raising=False)
    response = client.get("/metrics", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["content-encoding"] == "gzip"
    assert "novelai_sdk_info" in response.text

    only_info = client.get("/metrics", params={"name[]": "novelai_sdk_info"}).text
    assert "novelai_sdk_info" in only_info
    # client_python < 0.26 keeps the HELP/TYPE lines of filtered-out families; no series may remain
    assert "novelai_requests_total{" not in only_info

    openmetrics = client.get("/metrics", headers={"Accept": "application/openmetrics-text; version=1.0.0"})
    assert openmetrics.headers["content-type"].startswith("application/openmetrics-text")
    assert openmetrics.text.endswith("# EOF\n")

    monkeypatch.setenv("NOVELAI_METRICS_TOKEN", "s3cret")
    refused = client.get("/metrics")
    assert refused.status_code == 401
    assert refused.headers["www-authenticate"] == "Bearer"
    assert client.get("/metrics", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer s3cret"}).status_code == 200

    monkeypatch.setenv("NOVELAI_METRICS", "0")
    set_metrics(NovelAIMetrics())
    assert client.get("/metrics", headers={"Authorization": "Bearer s3cret"}).status_code == 404


# endregion
