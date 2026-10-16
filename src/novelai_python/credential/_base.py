# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : _shema.py


import secrets
import string
from datetime import UTC, datetime

from curl_cffi.requests import AsyncSession
from pydantic import BaseModel

# Browser identity sent with every request.
# Captured from the novelai.net web client (Chrome 155 / Windows; stable с 06.10.2026, цикл теперь 2 недели). Bump both
# values together when refreshing.
CHROME_MAJOR_VERSION = "155"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{CHROME_MAJOR_VERSION}.0.0.0 Safari/537.36"
)
DEFAULT_SEC_CH_UA = (
    # exact brand list and order Chrome 155 sends (HAR from the web client, 2026-10-16)
    f'"Google Chrome";v="{CHROME_MAJOR_VERSION}", "Chromium";v="{CHROME_MAJOR_VERSION}", "Not(A:Brand";v="24"'
)
# Accept-Language the captured client sent; override via browser_headers(accept_language=...)
DEFAULT_ACCEPT_LANGUAGE = "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,tr;q=0.6,zh-CN;q=0.5,zh;q=0.4,ja;q=0.3,zh-TW;q=0.2"
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
    Headers the novelai.net web client sends on API calls, in the order a real
    Chrome 155 emits them (HAR capture 2026-10-16). ``accept-encoding`` and
    ``content-length`` are added by curl itself.
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
        "sec-ch-ua-platform": '"Windows"',
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


class CredentialBase(BaseModel):
    _session: AsyncSession = None
    """会话"""
    proxy: str | None = None
    """Outbound proxy for every request, e.g. ``http://user:pass@host:port``
    (curl_cffi ``proxies`` for http and https). None = direct."""

    def session_kwargs(self, timeout: int, headers: dict) -> dict:
        # trust_env=False: never pick up HTTP(S)_PROXY from the environment — a
        # local system proxy (e.g. 127.0.0.1:2082 on a dev box) would silently
        # route NovelAI traffic and change the client's apparent address.
        kw = {"timeout": timeout, "headers": headers, "impersonate": IMPERSONATE, "trust_env": False}
        if self.proxy:
            kw["proxies"] = {"http": self.proxy, "https": self.proxy}
        return kw

    async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
        raise NotImplementedError
