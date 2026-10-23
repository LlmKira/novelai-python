"""Prometheus metrics for the SDK (optional: ``pip install "novelai-python[metrics]"``).

Every request the SDK sends is counted and timed; ``/user/subscription`` and ``/user/data``
responses also refresh per-account gauges (Anlas, subscription, the Opus usage bar). Without
``prometheus-client`` installed, or with ``NOVELAI_METRICS=0``, every call here is a no-op.

Names follow the Prometheus naming conventions that VictoriaMetrics recommends: base units
(seconds, ratios), counters end in ``_total``, timestamps in ``_timestamp_seconds``, and a quantity
split by a dimension is one metric with a label (``account_anlas{kind=...}``), not several metrics.
Every label has a small fixed set of values: an endpoint path, a model name, an HTTP status or one
of a few transport outcomes, a short account id. Prompts, seeds, tokens and job ids never become
label values.

The metrics live in a registry of the SDK's own, so an application's existing ``/metrics`` does not
change unless it asks: expose the SDK registry with :meth:`NovelAIMetrics.asgi_app` and friends, or
build the metrics with ``registry=prometheus_client.REGISTRY`` to merge them into the default one.
"""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import logging
import os
import threading
import time
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from curl_cffi.curl import CurlError

if TYPE_CHECKING:  # pragma: no cover
    import prometheus_client as prom
    from prometheus_client import CollectorRegistry

    from ._response.user.subscription import SubscriptionResp
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
DEFAULT_MAX_ACCOUNTS = 50
"""Accounts the per-account gauges track per process; further accounts are not recorded."""

REQUEST_BUCKETS = (0.1, 0.25, 0.5, 1, 2.5, 5, 10, 15, 30, 60, 120, 300)
"""Seconds. An account call takes well under a second, a generation 2-60 s, a queued one minutes."""
WAIT_BUCKETS = (0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60)
"""Seconds spent waiting in the pacer or before a retry."""

STATUS_STREAM_ERROR = "stream_error"
"""``status`` of a request whose HTTP 200 stream carried an error frame."""
STATUS_TIMEOUT = "timeout"
STATUS_DNS = "dns"
STATUS_PROXY = "proxy"
STATUS_CONNECT = "connect"
STATUS_SSL = "ssl"
STATUS_RESET = "reset"
STATUS_CANCELLED = "cancelled"
STATUS_TRANSPORT = "transport"
"""``status`` of a request without an HTTP answer that fits none of the other kinds."""
TRANSPORT_STATUSES = (
    STATUS_TIMEOUT,
    STATUS_DNS,
    STATUS_PROXY,
    STATUS_CONNECT,
    STATUS_SSL,
    STATUS_RESET,
    STATUS_CANCELLED,
    STATUS_TRANSPORT,
)
"""Every ``status`` value of a request that got no HTTP answer."""

# libcurl error codes, which curl_cffi errors carry in ``.code``
_CURL_CODES = {
    STATUS_TIMEOUT: frozenset({28}),  # OPERATION_TIMEDOUT
    STATUS_DNS: frozenset({6}),  # COULDNT_RESOLVE_HOST
    STATUS_PROXY: frozenset({5, 97}),  # COULDNT_RESOLVE_PROXY, PROXY
    STATUS_CONNECT: frozenset({7, 96}),  # COULDNT_CONNECT, QUIC_CONNECT_ERROR
    STATUS_SSL: frozenset({35, 53, 58, 59, 60, 77, 80, 82, 83, 90, 91, 98}),  # SSL_*, PEER_FAILED_VERIFICATION
    STATUS_RESET: frozenset(
        {16, 18, 52, 55, 56, 92}
    ),  # HTTP2, PARTIAL_FILE, GOT_NOTHING, SEND/RECV_ERROR, HTTP2_STREAM
}
# curl reports a refused proxy tunnel as a receive error (56); its message names the proxy
_PROXY_MARKERS = ("proxy", "connect tunnel", "socks")


def _enabled_by_env() -> bool:
    return os.environ.get(ENV_ENABLED, "1").strip().lower() not in ("0", "false", "no", "off")


def _multiprocess() -> bool:
    """client_python's multiprocess mode is on (it is chosen by this variable at import time)."""
    return "PROMETHEUS_MULTIPROC_DIR" in os.environ or "prometheus_multiproc_dir" in os.environ


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
    username or token are used, so an email never becomes a label value. A bare ``AsyncSession``
    has no account to name and is ``"session"``.
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


def _curl_status(error: CurlError) -> str:
    if any(marker in str(error).lower() for marker in _PROXY_MARKERS):
        return STATUS_PROXY
    try:
        code = int(error.code)
    except (TypeError, ValueError):
        return STATUS_TRANSPORT
    for status, codes in _CURL_CODES.items():
        if code in codes:
            return status
    return STATUS_TRANSPORT


def transport_label(exc: BaseException | None) -> str | None:
    """The ``status`` of a request that failed without an HTTP answer, or None when ``exc`` is not a
    transport failure: then no request went out (or the SDK has a bug) and nothing is counted.

    A curl error is found on the exception or its cause chain (the SDK wraps it in
    ``SessionHttpError``) and grouped by its libcurl code: ``timeout``, ``dns``, ``proxy`` (also a
    refused proxy tunnel), ``connect``, ``ssl``, ``reset`` (the connection broke mid-request) or else
    ``transport``. A cancelled task is ``cancelled``, a ``TimeoutError`` is ``timeout``. The set is
    fixed, so the label stays bounded.
    """
    seen: set[int] = set()
    cursor = exc
    while cursor is not None and id(cursor) not in seen:
        seen.add(id(cursor))
        if isinstance(cursor, asyncio.CancelledError):
            return STATUS_CANCELLED
        if isinstance(cursor, CurlError):
            return _curl_status(cursor)
        if isinstance(cursor, TimeoutError):
            return STATUS_TIMEOUT
        cursor = cursor.__cause__ or (None if cursor.__suppress_context__ else cursor.__context__)
    return None


class _Observation:
    """One timed request. Works with ``with`` and ``async with``; see :meth:`NovelAIMetrics.observe`.

    Call :meth:`report` inside the block with the HTTP status (or :data:`STATUS_STREAM_ERROR`). An
    exception that leaves the block before that is classified by :func:`transport_label`; one that is
    not a transport failure means no request went out, and nothing is counted.
    """

    __slots__ = ("_endpoint", "_metrics", "_model", "_started", "status")

    def __init__(self, metrics: NovelAIMetrics | None, endpoint: str, model: str) -> None:
        self._metrics = metrics  # None when metrics are disabled
        self._endpoint = endpoint
        self._model = model
        self._started = 0.0
        self.status: str | int | None = None

    def report(self, status: int | str) -> None:
        """The outcome: the HTTP status, or :data:`STATUS_STREAM_ERROR`."""
        self.status = status

    def __enter__(self) -> _Observation:
        if self._metrics is not None:
            self._started = time.perf_counter()
            self._metrics.in_flight.labels(self._endpoint).inc()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        m = self._metrics
        if m is None:
            return
        m.in_flight.labels(self._endpoint).dec()
        status = self.status if self.status is not None else transport_label(exc)
        if status is None:
            return
        m.requests.labels(self._endpoint, self._model, str(status)).inc()
        m.request_duration.labels(self._endpoint, self._model).observe(time.perf_counter() - self._started)
        if isinstance(status, int) and status < 400:
            m.last_success.labels(self._endpoint).set_to_current_time()

    async def __aenter__(self) -> _Observation:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.__exit__(exc_type, exc, tb)


class _AsgiApp:
    """client_python's ASGI app as an object, so ``app.add_route("/metrics", ...)`` works too.

    Starlette serves a plain function passed to ``add_route`` as a ``request -> response`` endpoint;
    client_python 0.26.0 and older return such a function, which then fails with a TypeError. An
    object is served as a raw ASGI app by ``add_route`` (exactly ``/metrics``) and by ``mount``
    (``/metrics/``, with a redirect from ``/metrics``).
    """

    __slots__ = ("_app",)

    def __init__(self, app: Callable) -> None:
        self._app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        await self._app(scope, receive, send)


if TYPE_CHECKING or PROMETHEUS_AVAILABLE:

    class _SdkRegistry(prom.CollectorRegistry):
        """The SDK's own registry. It leaves out the ``*_created`` samples client_python adds to every
        counter and histogram (unless asked to keep them): they double the series and
        VictoriaMetrics does not use them. Unlike ``disable_created_metrics()`` this does not change
        the metrics of the rest of the process."""

        def __init__(self, keep_created: bool) -> None:
            super().__init__()
            self._keep_created = keep_created

        def collect(self) -> Iterator[Any]:
            for family in super().collect():
                if not self._keep_created:
                    family.samples = [s for s in family.samples if not s.name.endswith("_created")]
                yield family


class NovelAIMetrics:
    """Every SDK metric in one registry. ``enabled`` is False without ``prometheus-client``."""

    def __init__(
        self,
        registry: CollectorRegistry | None = None,
        *,
        namespace: str = NAMESPACE,
        created_series: bool = False,
        process_metrics: bool = False,
        max_accounts: int = DEFAULT_MAX_ACCOUNTS,
    ) -> None:
        """
        :param registry: register the metrics there, e.g. ``prometheus_client.REGISTRY`` to show them
            on an application's existing ``/metrics``; default a registry of the SDK's own
        :param namespace: metric name prefix
        :param created_series: keep client_python's ``*_created`` series in the SDK's own registry
        :param process_metrics: add ``process_*``, ``python_info`` and ``python_gc_*`` to the SDK's own
            registry, for a process that serves only the SDK (the bundled server does)
        :param max_accounts: accounts the per-account gauges track; further accounts are not
            recorded, so a server used with many tokens cannot grow the series without bound
        """
        self.enabled = PROMETHEUS_AVAILABLE and _enabled_by_env()
        self.namespace = namespace
        self.max_accounts = max_accounts
        self._accounts: set[str] = set()
        self._accounts_lock = threading.Lock()
        self._accounts_warned = False
        self._limiter: Any = None
        self._multiprocess = _multiprocess()
        self.registry: CollectorRegistry | None
        if not self.enabled:
            self.registry = None
            return
        if registry is None:
            self.registry = _SdkRegistry(keep_created=created_series)
            if process_metrics:
                prom.ProcessCollector(registry=self.registry)
                prom.PlatformCollector(registry=self.registry)
                prom.GCCollector(registry=self.registry)
        else:
            self.registry = registry
        ns, reg = namespace, self.registry

        # requests
        self.requests = prom.Counter(
            "requests_total",
            "Requests sent to NovelAI by endpoint path, model and outcome: the HTTP status, "
            + ", ".join(TRANSPORT_STATUSES)
            + f" when no HTTP answer came, or {STATUS_STREAM_ERROR} for an error frame in a 200 stream.",
            ["endpoint", "model", "status"],
            namespace=ns,
            registry=reg,
        )
        self.request_duration = prom.Histogram(
            "request_duration_seconds",
            "Wall time of one request, the proxy included, until the response or the whole stream is read.",
            ["endpoint", "model"],
            namespace=ns,
            registry=reg,
            buckets=REQUEST_BUCKETS,
        )
        self.in_flight = prom.Gauge(
            "requests_in_flight",
            "Requests sent to NovelAI and not answered yet.",
            ["endpoint"],
            namespace=ns,
            registry=reg,
            multiprocess_mode="livesum",
        )
        self.last_success = prom.Gauge(
            "last_success_timestamp_seconds",
            "Unix time an endpoint last answered with a status below 400.",
            ["endpoint"],
            namespace=ns,
            registry=reg,
            multiprocess_mode="max",
        )
        self.images = prom.Counter(
            "images_total",
            "Images received: ZIP entries, bare images and final stream frames.",
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
            "Retries of a request that got HTTP 500 (retry_on_server_error).",
            ["endpoint"],
            namespace=ns,
            registry=reg,
        )
        self.retry_wait = prom.Histogram(
            "retry_wait_seconds",
            "Backoff slept before a retry.",
            namespace=ns,
            registry=reg,
            buckets=WAIT_BUCKETS,
        )
        self.pacing_wait = prom.Histogram(
            "pacing_wait_seconds",
            "Time a request waited for the gap after the previous one (RequestPacer); 0 when none was left.",
            namespace=ns,
            registry=reg,
            buckets=WAIT_BUCKETS,
        )
        self.limit_remaining = prom.Gauge(
            "local_limit_remaining_images",
            "Images left in the window of the local DailyImageLimiter last used; -1 before one is used or when it is off.",
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        if self._multiprocess:
            self.limit_remaining.set(-1)  # set on use: a scrape-time callback is not shared between processes
        else:
            self.limit_remaining.set_function(self._limit_remaining)

        # accounts: refreshed by /user/subscription and /user/data responses
        account = ["account"]
        self.account_anlas = prom.Gauge(
            "account_anlas",
            "Anlas left by kind: fixed (the monthly allowance, reset at renewal) and purchased (never expire). "
            "Their sum is what the account can spend.",
            ["account", "kind"],
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.tier = prom.Gauge(
            "subscription_tier",
            "Subscription tier: 0 Paper, 1 Tablet, 2 Scroll, 3 Opus.",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.active = prom.Gauge(
            "subscription_active",
            "1 while the subscription is active.",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.expires = prom.Gauge(
            "subscription_expires_timestamp_seconds",
            "Unix time the subscription expires.",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.usage_ratio = prom.Gauge(
            "opus_usage_ratio",
            "The Opus usage bar for V5 as a ratio (0.42 = 42 %); above 1 after bonuses.",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.usage_negative = prom.Gauge(
            "opus_usage_negative",
            "1 while the usage bar is below zero and V5 costs Anlas.",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.usage_refill = prom.Gauge(
            "opus_usage_refill_ratio_per_second",
            "How fast the usage bar refills, as a ratio per second; 0 while the refill is paused. "
            "Multiply by 8640000 for percent per day.",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.usage_images = prom.Gauge(
            "opus_images_left",
            "Estimated free V5 images the usage bar still covers (the web client counts 17.3 per percent).",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="mostrecent",
        )
        self.account_updated = prom.Gauge(
            "account_updated_timestamp_seconds",
            "Unix time the account gauges were last refreshed.",
            account,
            namespace=ns,
            registry=reg,
            multiprocess_mode="max",
        )
        self._usage_gauges = (self.usage_ratio, self.usage_negative, self.usage_refill, self.usage_images)
        self.info = prom.Info(
            "sdk", "SDK version and the browser whose TLS fingerprint it uses.", namespace=ns, registry=reg
        )
        self.info.info(_sdk_info())

    # region observing

    def observe(self, url: str, model: Any = None) -> _Observation:
        """Time one request: ``with metrics.observe(url, model) as obs:`` or ``async with``.
        Call ``obs.report(status)`` inside, right after the response arrives."""
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
            self.retry_wait.observe(max(0.0, wait_seconds))

    def observe_pacing_wait(self, wait_seconds: float) -> None:
        if self.enabled:
            self.pacing_wait.observe(max(0.0, wait_seconds))

    def observe_limiter(self, limiter: Any) -> None:
        """Remember the limiter a request used; the gauge reads it at scrape time."""
        if not self.enabled or limiter is None:
            return
        self._limiter = limiter
        if self._multiprocess:
            self.limit_remaining.set(self._limit_remaining())

    def _limit_remaining(self) -> float:
        limiter = self._limiter
        if limiter is None:
            return -1
        try:
            return float(limiter.remaining)
        except Exception as exc:  # the gauge is a convenience: never fail a scrape
            logger.debug(f"limiter gauge not read: {exc!r}")
            return -1

    def observe_subscription(self, subscription: SubscriptionResp | None, account: str) -> None:
        """Refresh the account gauges from a ``/user/subscription`` (or ``/user/data``) response."""
        if not self.enabled or subscription is None or not self._track_account(account):
            return
        steps = subscription.trainingStepsLeft
        self.account_anlas.labels(account, "fixed").set(steps.fixedTrainingStepsLeft)
        self.account_anlas.labels(account, "purchased").set(steps.purchasedTrainingSteps)
        self.tier.labels(account).set(subscription.tier)
        self.active.labels(account).set(1 if subscription.is_active else 0)
        self.expires.labels(account).set(subscription.expiresAt)
        usage = subscription.usage
        if usage is None:
            # not (or no longer) on Opus: no usage bar, rather than the last one frozen
            if not self._multiprocess:  # client_python cannot remove series in multiprocess mode
                for gauge in self._usage_gauges:
                    gauge.remove(account)
        else:
            self.usage_ratio.labels(account).set(usage.percent / 100)
            self.usage_negative.labels(account).set(1 if usage.isNegative else 0)
            period = usage.timeUntilNextPercent  # seconds per +1 %; 0 while paused
            self.usage_refill.labels(account).set(0.01 / period if period else 0)
            self.usage_images.labels(account).set(usage.images_left_estimate)
        self.account_updated.labels(account).set_to_current_time()

    def _track_account(self, account: str) -> bool:
        with self._accounts_lock:
            if account in self._accounts:
                return True
            if len(self._accounts) < self.max_accounts:
                self._accounts.add(account)
                return True
            first = not self._accounts_warned
            self._accounts_warned = True
        if first:
            logger.warning(
                f"More than {self.max_accounts} NovelAI accounts in this process: the account gauges "
                "skip the others (NovelAIMetrics(max_accounts=...))"
            )
        return False

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

    def asgi_app(self, disable_compression: bool = False) -> _AsgiApp:
        """An ASGI app serving the registry: ``app.add_route("/metrics", metrics.asgi_app())`` serves
        exactly ``/metrics``, ``app.mount("/metrics", ...)`` serves ``/metrics/``. It gzips for
        scrapers that accept it, answers OpenMetrics when asked and honours ``?name[]=`` filters."""
        return _AsgiApp(prom.make_asgi_app(registry=self._require(), disable_compression=disable_compression))

    def wsgi_app(self, disable_compression: bool = False):
        return prom.make_wsgi_app(registry=self._require(), disable_compression=disable_compression)

    def start_http_server(self, port: int, addr: str = "0.0.0.0", **kwargs):
        """Serve the registry from a daemon thread; ``certfile=`` and ``keyfile=`` switch it to HTTPS
        (see ``prometheus_client.start_http_server``). It has no authentication: bind it to a
        private address."""
        return prom.start_http_server(port, addr=addr, registry=self._require(), **kwargs)

    def write_textfile(self, path: str) -> None:
        """Atomic write for the node_exporter / vmagent textfile collector (``path`` ends in ``.prom``)."""
        prom.write_to_textfile(path, self._require())

    def push_to_victoriametrics(
        self,
        base_url: str,
        *,
        extra_labels: dict[str, str] | None = None,
        timeout: float = 10,
        compress: bool = True,
    ) -> None:
        """POST the registry to ``<base_url>/api/v1/import/prometheus`` (VictoriaMetrics or vmagent).

        Pull (a scrape of :meth:`asgi_app`) is the better default: the scraper sets the resolution
        and ``up == 0`` tells when the process is gone. Pushing fits short-lived scripts.
        ``extra_labels`` become ``extra_label=name=value`` query arguments, e.g. ``job`` and
        ``instance``. The body is gzip-compressed unless ``compress=False``. VictoriaMetrics imports
        the stream without reporting bad lines in the response: they show up in its
        ``vm_rows_invalid_total`` counter.
        """
        import urllib.parse
        import urllib.request

        self._require()
        query = "&".join(
            f"extra_label={urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k, v in (extra_labels or {}).items()
        )
        url = base_url.rstrip("/") + "/api/v1/import/prometheus" + (f"?{query}" if query else "")
        body = self.generate_latest()
        request = urllib.request.Request(url, data=gzip.compress(body) if compress else body, method="POST")
        request.add_header("Content-Type", "text/plain; charset=utf-8")
        if compress:
            request.add_header("Content-Encoding", "gzip")
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
_default_lock = threading.Lock()


def get_metrics() -> NovelAIMetrics:
    """The process-wide metrics (created on first use)."""
    global _default
    with _default_lock:
        if _default is None:
            _default = NovelAIMetrics()
        return _default


def set_metrics(metrics: NovelAIMetrics | None) -> None:
    """Replace the process-wide metrics, e.g. with ``NovelAIMetrics(registry=prometheus_client.REGISTRY)``.
    Call it before the first request: metrics already recorded stay in the old registry."""
    global _default
    with _default_lock:
        _default = metrics


__all__ = [
    "DEFAULT_MAX_ACCOUNTS",
    "ENV_ENABLED",
    "PROMETHEUS_AVAILABLE",
    "REQUEST_BUCKETS",
    "STATUS_CANCELLED",
    "STATUS_CONNECT",
    "STATUS_DNS",
    "STATUS_PROXY",
    "STATUS_RESET",
    "STATUS_SSL",
    "STATUS_STREAM_ERROR",
    "STATUS_TIMEOUT",
    "STATUS_TRANSPORT",
    "TRANSPORT_STATUSES",
    "WAIT_BUCKETS",
    "NovelAIMetrics",
    "account_label",
    "endpoint_label",
    "get_metrics",
    "model_label",
    "set_metrics",
    "short_hash",
    "transport_label",
]
