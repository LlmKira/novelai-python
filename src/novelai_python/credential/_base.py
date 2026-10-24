# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : _shema.py


import secrets
import string
from datetime import UTC, datetime

from curl_cffi.requests import AsyncSession
from pydantic import BaseModel, Field

ACCEPT_LANGUAGES = {
    "en": "en-US,en;q=0.9",
    "en-sg": "en-SG,en;q=0.9",
    "en-gb": "en-GB,en;q=0.9",
    "ja": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "zh": "zh-CN,zh;q=0.9,en;q=0.8",
    "ko": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "ru": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}
"""Accept-Language values Chrome sends for common browser languages. English is the default."""
DEFAULT_ACCEPT_LANGUAGE = ACCEPT_LANGUAGES["en"]


def resolve_accept_language(value: str | None) -> str:
    """A key of ACCEPT_LANGUAGES ("en-sg") or a full Accept-Language header value."""
    if not value:
        return DEFAULT_ACCEPT_LANGUAGE
    return ACCEPT_LANGUAGES.get(value.lower(), value)


_CORR_ALPHABET = string.ascii_letters + string.digits


def _correlation_id() -> str:
    """6-char x-correlation-id as the web client sends it (e.g. ``ps1i9W``)."""
    return "".join(secrets.choice(_CORR_ALPHABET) for _ in range(6))


def _initiated_at() -> str:
    """x-initiated-at in the web client format: 2026-10-16T15:54:25.576Z"""
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


NOVELAI_WEB_ORIGIN = "https://novelai.net"


def browser_headers(
    extra: dict[str, str] | None = None, accept_language: str = DEFAULT_ACCEPT_LANGUAGE
) -> dict[str, str]:
    """
    Headers the novelai.net web client sends on API calls, in the order Chrome emits
    them. ``accept-encoding`` and ``content-length`` are added by curl itself.
    :param extra: headers merged on top (e.g. Authorization)
    :param accept_language: Accept-Language of the simulated browser profile
    :return: dict
    """
    headers = {
        "accept": "*/*",
        "accept-language": accept_language,
        "cache-control": "no-cache",
        "origin": NOVELAI_WEB_ORIGIN,
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": f"{NOVELAI_WEB_ORIGIN}/",
        "sec-ch-ua": DEFAULT_SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": SEC_CH_UA_PLATFORM,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": DEFAULT_USER_AGENT,
    }
    if extra:
        headers.update({k.lower(): v for k, v in extra.items()})
    return headers


def get_impersonate_target() -> str:
    """
    Newest Chrome TLS fingerprint the installed curl_cffi can impersonate.
    Falls back to chrome136 on old curl_cffi builds.
    """
    try:
        from curl_cffi.requests.impersonate import DEFAULT_CHROME

        return str(DEFAULT_CHROME)
    except Exception:
        return "chrome136"


IMPERSONATE = get_impersonate_target()


def chrome_brands(major: int) -> str:
    """sec-ch-ua as Chrome builds it for a major version (GREASE brand, version and order are seeded by it)."""
    chars = [" ", "(", ":", "-", ".", "/", ")", ";", "=", "?", "_"]
    grease = (
        f'"Not{chars[major % len(chars)]}A{chars[(major + 1) % len(chars)]}Brand";v="{["8", "99", "24"][major % 3]}"'
    )
    orders = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]]
    order = orders[major % len(orders)]
    brands = ["", "", ""]
    brands[order[0]] = grease
    brands[order[1]] = f'"Chromium";v="{major}"'
    brands[order[2]] = f'"Google Chrome";v="{major}"'
    return ", ".join(brands)


# The browser the headers describe: the Chrome on Windows that novelai.net users run now.
# curl_cffi's newest TLS profile can lag a few versions behind; its ClientHello still matches
# this Chrome except for extensions added since (Chrome's ClientHello does not depend on the OS).
CHROME_MAJOR_VERSION = "155"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{CHROME_MAJOR_VERSION}.0.0.0 Safari/537.36"
)
DEFAULT_SEC_CH_UA = chrome_brands(int(CHROME_MAJOR_VERSION))
SEC_CH_UA_PLATFORM = '"Windows"'


class CredentialBase(BaseModel):
    proxy: str | None = Field(default=None, repr=False)  # may carry user:password
    """Outbound proxy for every request, e.g. ``http://user:pass@host:port``
    (curl_cffi ``proxies`` for http and https). None = direct."""
    accept_language: str | None = None
    """Browser language: a key of ``ACCEPT_LANGUAGES`` (``"en-sg"``, ``"ja"``, ...) or a full
    Accept-Language value. None = English (``en-US,en;q=0.9``). Match it to the proxy's country."""
    metrics_label: str | None = Field(default=None, description="account label of this credential in the metrics")
    """Value of the ``account`` label on the Anlas / usage gauges (``novelai_python.metrics``).
    None = the first 8 hex digits of a SHA-256 of the username or token: stable, and not the email."""

    def metrics_account(self) -> str:
        """``metrics_label``, else a short hash of what identifies the account (``_metrics_seed``)."""
        if self.metrics_label:
            return self.metrics_label
        seed = self._metrics_seed()
        if not seed:
            return "unknown"
        from ..metrics import short_hash

        return short_hash(seed)

    def _metrics_seed(self) -> str | None:
        return None

    def session_kwargs(self, timeout: int, headers: dict) -> dict:
        # trust_env=False: never pick up HTTP(S)_PROXY from the environment. A
        # system-wide proxy on the machine would silently route NovelAI traffic
        # and change the client's apparent address.
        headers = {**headers, "accept-language": resolve_accept_language(self.accept_language)}
        kw = {"timeout": timeout, "headers": headers, "impersonate": IMPERSONATE, "trust_env": False}
        if self.proxy:
            kw["proxies"] = {"http": self.proxy, "https": self.proxy}
        return kw

    async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
        raise NotImplementedError


class BearerCredential(CredentialBase):
    """A credential that sends ``Authorization: Bearer <token>``; subclasses say where the token is."""

    x_correlation_id: str = Field(default_factory=_correlation_id)

    def _token(self) -> str:
        raise NotImplementedError

    def _metrics_seed(self) -> str | None:
        return self._token()

    async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
        # update_headers goes through browser_headers too: its lowercased keys replace ours
        headers = browser_headers(
            {
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json",
                "x-correlation-id": self.x_correlation_id,
                "x-initiated-at": _initiated_at(),
                **(update_headers or {}),
            }
        )
        return AsyncSession(**self.session_kwargs(timeout, headers))
