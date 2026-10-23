"""Prometheus metrics for the SDK (optional: ``pip install "novelai-python[metrics]"``).

Every request the SDK sends is observed; the account endpoints also publish the Anlas balance and
the Opus usage bar as gauges. Without ``prometheus-client`` installed, or with ``NOVELAI_METRICS=0``,
every call here is a no-op.

Names follow the Prometheus conventions that VictoriaMetrics documents too: counters end in
``_total``, durations are seconds, timestamps are ``_timestamp_seconds``. Labels are bounded
(an endpoint path, a model name, an HTTP status, a short account id): no prompts, tokens or
job ids ever become a label.

Expose the registry with :meth:`NovelAIMetrics.asgi_app` / :meth:`NovelAIMetrics.start_http_server`
for a vmagent/Prometheus scrape, or push a snapshot with :meth:`NovelAIMetrics.push_to_victoriametrics`.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

if TYPE_CHECKING:  # pragma: no cover
    from prometheus_client import CollectorRegistry

    from ._response.user.subscription import SubscriptionResp

if TYPE_CHECKING:  # pragma: no cover
    import prometheus_client as prom
else:
    try:
        import prometheus_client as prom
    except ImportError:  # the extra is optional
        prom = None

PROMETHEUS_AVAILABLE = prom is not None

logger = logging.getLogger(__name__)

ENV_ENABLED = "NOVELAI_METRICS"
"""``0`` / ``false`` disables metrics even when ``prometheus-client`` is installed."""
NAMESPACE = "novelai"

REQUEST_BUCKETS = (0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 60, 120, 300)
"""Seconds. A generation takes 2-60 s, an account call well under a second."""
WAIT_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 60)
"""Seconds spent waiting in the pacer or before a retry."""

STATUS_TRANSPORT = "transport"
"""``status`` label when no HTTP status came back (SSL, DNS, timeout, aborted stream)."""
STATUS_STREAM_ERROR = "stream_error"
"""``status`` label for an error frame inside an HTTP 200 stream."""


def _enabled_by_env() -> bool:
    return os.environ.get(ENV_ENABLED, "1").strip().lower() not in ("0", "false", "no", "off")


def endpoint_label(url: str) -> str:
    """The path of a NovelAI URL (``/ai/generate-image``): one label value per endpoint."""
    path = urlsplit(url).path or "/"
    return path.rstrip("/") or "/"


def model_label(model: Any) -> str:
    """The wire name of a model enum or string; ``""`` for endpoints without a model."""
    if model is None:
        return ""
    return str(getattr(model, "value", model))


def account_label(session: Any) -> str:
    """A short, stable, non-identifying id of the account a session belongs to.

    Credentials can set ``metrics_label``; otherwise the first 8 hex digits of a SHA-256 of the
    username or token are used, so an email never becomes a label value.
    """
    getter = getattr(session, "metrics_account", None)
    if callable(getter):
        try:
            return str(getter())
        except Exception:  # a credential is never required to support this
            return "unknown"
    return "session"


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


class _Observation:
    """One timed request. Works with ``with`` and ``async with``; see :meth:`NovelAIMetrics.observe`.

    Call :meth:`ok` or :meth:`failed` inside the block. An exception that leaves the block before
    either was called counts as ``'transport'``.
    """

    __slots__ = ("_endpoint", "_metrics", "_model", "_started", "status")

    def __init__(self, metrics: NovelAIMetrics | None, endpoint: str, model: str) -> None:
        self._metrics = metrics  # None when metrics are disabled
        self._endpoint = endpoint
        self._model = model
        self._started = 0.0
        self.status: str | int | None = None

    def ok(self, status: int = 200) -> None:
        self.status = status

    def failed(self, status: str | int) -> None:
        self.status = status

    def __enter__(self) -> _Observation:
        if self._metrics is not None:
            self._started = time.perf_counter()
            self._metrics.inflight.labels(self._endpoint).inc()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._metrics is None:
            return
        m = self._metrics
        m.inflight.labels(self._endpoint).dec()
        status = self.status if self.status is not None else STATUS_TRANSPORT
        m.requests.labels(self._endpoint, self._model, str(status)).inc()
        m.request_seconds.labels(self._endpoint, self._model).observe(time.perf_counter() - self._started)
        if isinstance(status, int) and status < 400:
            m.last_success.labels(self._endpoint).set(time.time())

    async def __aenter__(self) -> _Observation:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.__exit__(exc_type, exc, tb)


class NovelAIMetrics:
    """One registry with every SDK metric. ``enabled`` is False without ``prometheus-client``."""

    def __init__(self, registry: CollectorRegistry | None = None, *, namespace: str = NAMESPACE) -> None:
        self.enabled = PROMETHEUS_AVAILABLE and _enabled_by_env()
        self.namespace = namespace
        if not self.enabled:
            self.registry = None
            return
        self.registry = registry if registry is not None else prom.CollectorRegistry()
        ns = namespace
        reg = self.registry
        self.requests = prom.Counter(
            "requests_total",
            "Requests sent to NovelAI by endpoint path, model and outcome (HTTP status, "
            f"'{STATUS_TRANSPORT}' or '{STATUS_STREAM_ERROR}').",
            ["endpoint", "model", "status"],
            namespace=ns,
            registry=reg,
        )
        self.request_seconds = prom.Histogram(
            "request_seconds",
            "Wall time of one request including the proxy and reading the response.",
            ["endpoint", "model"],
            namespace=ns,
            registry=reg,
            buckets=REQUEST_BUCKETS,
        )
        self.inflight = prom.Gauge(
            "inflight_requests",
            "Requests currently waiting for NovelAI.",
            ["endpoint"],
            namespace=ns,
            registry=reg,
        )
        self.images = prom.Counter(
            "images_total",
            "Images received (ZIP entries, bare images or final stream frames).",
            ["model"],
            namespace=ns,
            registry=reg,
        )
        self.stream_frames = prom.Counter(
            "stream_frames_total",
            "Frames received from /ai/generate-image-stream, previews included.",
            ["model"],
            namespace=ns,
            registry=reg,
        )
        self.retries = prom.Counter(
            "retries_total",
            "Retries after an HTTP 500 (retry_on_server_error).",
            ["endpoint"],
            namespace=ns,
            registry=reg,
        )
        self.retry_wait_seconds = prom.Histogram(
            "retry_wait_seconds",
            "Backoff slept before a retry.",
            namespace=ns,
            registry=reg,
            buckets=WAIT_BUCKETS,
        )
        self.pacing_wait_seconds = prom.Histogram(
            "pacing_wait_seconds",
            "Time a request waited for the gap after the previous one (RequestPacer); 0 when none was needed.",
            namespace=ns,
            registry=reg,
            buckets=WAIT_BUCKETS,
        )
        self.last_success = prom.Gauge(
            "last_success_timestamp_seconds",
            "Unix time of the last successful request per endpoint.",
            ["endpoint"],
            namespace=ns,
            registry=reg,
        )
        self.limit_remaining = prom.Gauge(
            "local_limit_remaining_images",
            "Images left in the local DailyImageLimiter window (-1 when the limiter is off).",
            namespace=ns,
            registry=reg,
        )
        # account state: refreshed by /user/subscription and /user/data responses
        account = ["account"]
        self.anlas = prom.Gauge(
            "anlas_available", "Anlas the account can spend (fixed + purchased).", account, namespace=ns, registry=reg
        )
        self.anlas_fixed = prom.Gauge(
            "anlas_fixed", "Monthly Anlas left; reset, not added, at renewal.", account, namespace=ns, registry=reg
        )
        self.anlas_purchased = prom.Gauge(
            "anlas_purchased", "Purchased Anlas left; these do not expire.", account, namespace=ns, registry=reg
        )
        self.tier = prom.Gauge(
            "subscription_tier", "0 Paper, 1 Tablet, 2 Scroll, 3 Opus.", account, namespace=ns, registry=reg
        )
        self.active = prom.Gauge(
            "subscription_active", "1 while the subscription is active.", account, namespace=ns, registry=reg
        )
        self.expires = prom.Gauge(
            "subscription_expires_timestamp_seconds",
            "Unix time the subscription expires.",
            account,
            namespace=ns,
            registry=reg,
        )
        self.usage_percent = prom.Gauge(
            "opus_usage_percent",
            "Opus usage bar for V5 in percent; may exceed 100 after bonuses.",
            account,
            namespace=ns,
            registry=reg,
        )
        self.usage_negative = prom.Gauge(
            "opus_usage_negative",
            "1 while the usage bar is below zero and V5 costs Anlas.",
            account,
            namespace=ns,
            registry=reg,
        )
        self.usage_refill = prom.Gauge(
            "opus_usage_refill_percent_per_day",
            "How fast the usage bar refills, in percent per day.",
            account,
            namespace=ns,
            registry=reg,
        )
        self.usage_images = prom.Gauge(
            "opus_images_left",
            "Free V5 images the usage bar still covers (about 17.3 per percent).",
            account,
            namespace=ns,
            registry=reg,
        )
        self.account_updated = prom.Gauge(
            "account_updated_timestamp_seconds",
            "Unix time the account gauges were last refreshed.",
            account,
            namespace=ns,
            registry=reg,
        )
        self.info = prom.Info("sdk", "SDK version and browser impersonation target.", namespace=ns, registry=reg)
        self.info.info(_sdk_info())

    # region observing

    def observe(self, url: str, model: Any = None) -> _Observation:
        """Time one request: ``with metrics.observe(url, model) as obs:`` or ``async with``.
        Call ``obs.ok(status)`` or ``obs.failed(status)`` inside; an exception that leaves the
        block counts as ``'transport'`` unless a status was set."""
        if not self.enabled:
            return _Observation(None, "", "")
        return _Observation(self, endpoint_label(url), model_label(model))

    def observe_images(self, model: Any, count: int) -> None:
        if self.enabled and count > 0:
            self.images.labels(model_label(model)).inc(count)

    def observe_stream_frame(self, model: Any) -> None:
        if self.enabled:
            self.stream_frames.labels(model_label(model)).inc()

    def observe_retry(self, url: str, wait_seconds: float) -> None:
        if self.enabled:
            self.retries.labels(endpoint_label(url)).inc()
            self.retry_wait_seconds.observe(max(0.0, wait_seconds))

    def observe_pacing_wait(self, wait_seconds: float) -> None:
        if self.enabled:
            self.pacing_wait_seconds.observe(max(0.0, wait_seconds))

    def observe_limiter(self, limiter: Any) -> None:
        if self.enabled and limiter is not None:
            try:
                self.limit_remaining.set(limiter.remaining)
            except Exception as exc:  # the gauge is a convenience, never a failure
                logger.debug(f"limiter gauge not updated: {exc!r}")

    def observe_subscription(self, subscription: SubscriptionResp | None, account: str) -> None:
        """Refresh the account gauges from a ``/user/subscription`` (or ``/user/data``) response."""
        if not self.enabled or subscription is None:
            return
        steps = subscription.trainingStepsLeft
        self.anlas.labels(account).set(subscription.anlas_left)
        self.anlas_fixed.labels(account).set(steps.fixedTrainingStepsLeft)
        self.anlas_purchased.labels(account).set(steps.purchasedTrainingSteps)
        self.tier.labels(account).set(subscription.tier)
        self.active.labels(account).set(1 if subscription.is_active else 0)
        self.expires.labels(account).set(subscription.expiresAt)
        usage = subscription.usage
        if usage is not None:
            self.usage_percent.labels(account).set(usage.percent)
            self.usage_negative.labels(account).set(1 if usage.isNegative else 0)
            refill = usage.refill_percent_per_day
            self.usage_refill.labels(account).set(refill if refill is not None else 0)
            self.usage_images.labels(account).set(usage.images_left_estimate)
        self.account_updated.labels(account).set(time.time())

    # endregion

    # region exposing

    def generate_latest(self) -> bytes:
        """The registry in the Prometheus text exposition format (empty bytes when disabled)."""
        if not self.enabled or self.registry is None:
            return b""
        return prom.generate_latest(self.registry)

    @property
    def content_type(self) -> str:
        return prom.CONTENT_TYPE_LATEST if self.enabled else "text/plain; charset=utf-8"

    def asgi_app(self, disable_compression: bool = False):
        """An ASGI app for ``app.mount("/metrics", metrics.asgi_app())`` (FastAPI / Starlette)."""
        return prom.make_asgi_app(registry=self._require(), disable_compression=disable_compression)

    def wsgi_app(self, disable_compression: bool = False):
        return prom.make_wsgi_app(registry=self._require(), disable_compression=disable_compression)

    def start_http_server(self, port: int, addr: str = "0.0.0.0", **kwargs):
        """Serve the registry from a daemon thread (``prometheus_client.start_http_server``)."""
        return prom.start_http_server(port, addr=addr, registry=self._require(), **kwargs)

    def write_textfile(self, path: str) -> None:
        """Atomic write for the node_exporter / vmagent textfile collector."""
        prom.write_to_textfile(path, self._require())

    def push_to_victoriametrics(
        self, base_url: str, *, extra_labels: dict[str, str] | None = None, timeout: float = 10
    ) -> None:
        """POST the registry to ``<base_url>/api/v1/import/prometheus`` (VictoriaMetrics or vmagent).

        Pull (a scrape of :meth:`asgi_app`) is the better default; pushing fits short-lived scripts.
        ``extra_labels`` become ``extra_label=name=value`` query arguments.
        """
        import urllib.parse
        import urllib.request

        self._require()
        query = "&".join(
            f"extra_label={urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k, v in (extra_labels or {}).items()
        )
        url = base_url.rstrip("/") + "/api/v1/import/prometheus" + (f"?{query}" if query else "")
        request = urllib.request.Request(url, data=self.generate_latest(), method="POST")
        request.add_header("Content-Type", "text/plain; charset=utf-8")
        # no proxy from the environment: a system proxy must not learn about the monitoring host
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=timeout) as response:
            if response.status >= 300:
                raise RuntimeError(f"VictoriaMetrics import answered HTTP {response.status}")

    # endregion

    def _require(self) -> CollectorRegistry:
        if not self.enabled or self.registry is None:
            raise RuntimeError(
                'Metrics are off: install the extra (pip install "novelai-python[metrics]") '
                f"and do not set {ENV_ENABLED}=0"
            )
        return self.registry


def _sdk_info() -> dict[str, str]:
    from importlib.metadata import PackageNotFoundError, version

    try:
        sdk_version = version("novelai-python")
    except PackageNotFoundError:  # running from a checkout
        sdk_version = "unknown"
    try:
        from .credential._base import IMPERSONATE

        impersonate = str(IMPERSONATE)
    except Exception:
        impersonate = "unknown"
    return {"version": sdk_version, "impersonate": impersonate}


_default: NovelAIMetrics | None = None


def get_metrics() -> NovelAIMetrics:
    """The process-wide metrics (created on first use)."""
    global _default
    if _default is None:
        _default = NovelAIMetrics()
    return _default


def set_metrics(metrics: NovelAIMetrics | None) -> None:
    """Replace the process-wide metrics, e.g. to use your own ``CollectorRegistry``."""
    global _default
    _default = metrics


__all__ = [
    "ENV_ENABLED",
    "PROMETHEUS_AVAILABLE",
    "REQUEST_BUCKETS",
    "STATUS_STREAM_ERROR",
    "STATUS_TRANSPORT",
    "NovelAIMetrics",
    "account_label",
    "endpoint_label",
    "get_metrics",
    "model_label",
    "set_metrics",
    "short_hash",
]
