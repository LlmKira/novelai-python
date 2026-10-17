# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : _shema.py


import secrets
import string
from datetime import UTC, datetime

from curl_cffi.requests import AsyncSession
from pydantic import BaseModel

DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9"
"""Accept-Language of the simulated browser; override via browser_headers(accept_language=...)."""
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
    them. The browser version and OS follow the curl_cffi impersonate target, so the
    headers and the TLS fingerprint describe the same browser. ``accept-encoding`` and
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


def _target_os(target: str) -> str:
    """OS of the curl_cffi profile; the headers have to claim the same one as the TLS fingerprint."""
    try:
        from curl_cffi.fingerprints import NATIVE_IMPERSONATE_TARGETS

        for fp in NATIVE_IMPERSONATE_TARGETS:
            if fp.get("target_name") == target:
                return str(fp.get("os") or "Windows")
    except Exception:
        pass
    return "Windows"


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


CHROME_MAJOR_VERSION = "".join(c for c in IMPERSONATE if c.isdigit()) or "136"
_OS = _target_os(IMPERSONATE)
_UA_PLATFORM = "Macintosh; Intel Mac OS X 10_15_7" if _OS == "macOS" else "Windows NT 10.0; Win64; x64"
DEFAULT_USER_AGENT = (
    f"Mozilla/5.0 ({_UA_PLATFORM}) AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{CHROME_MAJOR_VERSION}.0.0.0 Safari/537.36"
)
DEFAULT_SEC_CH_UA = chrome_brands(int(CHROME_MAJOR_VERSION))
SEC_CH_UA_PLATFORM = '"macOS"' if _OS == "macOS" else '"Windows"'


class CredentialBase(BaseModel):
    _session: AsyncSession | None = None
    """会话"""
    proxy: str | None = None
    """Outbound proxy for every request, e.g. ``http://user:pass@host:port``
    (curl_cffi ``proxies`` for http and https). None = direct."""

    def session_kwargs(self, timeout: int, headers: dict) -> dict:
        # trust_env=False: never pick up HTTP(S)_PROXY from the environment. A
        # system-wide proxy on the machine would silently route NovelAI traffic
        # and change the client's apparent address.
        kw = {"timeout": timeout, "headers": headers, "impersonate": IMPERSONATE, "trust_env": False}
        if self.proxy:
            kw["proxies"] = {"http": self.proxy, "https": self.proxy}
        return kw

    async def get_session(self, timeout: int = 180, update_headers: dict | None = None):
        raise NotImplementedError
