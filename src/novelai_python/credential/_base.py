# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : _shema.py

from typing import Dict, Optional

from curl_cffi.requests import AsyncSession
from fake_useragent import UserAgent
from pydantic import BaseModel

FAKE_UA = UserAgent()

# Browser identity sent with every request.
# Captured from the novelai.net web client (Chrome 155 / Windows; stable с 06.10.2026, цикл теперь 2 недели). Bump both
# values together when refreshing.
CHROME_MAJOR_VERSION = "155"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{CHROME_MAJOR_VERSION}.0.0.0 Safari/537.36"
)
DEFAULT_SEC_CH_UA = (
    f'"Chromium";v="{CHROME_MAJOR_VERSION}", "Google Chrome";v="{CHROME_MAJOR_VERSION}", "Not A(Brand";v="99"'
)
NOVELAI_WEB_ORIGIN = "https://novelai.net"


def browser_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Headers that the novelai.net web client sends on API calls.
    :param extra: headers merged on top (e.g. Authorization)
    :return: dict
    """
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": NOVELAI_WEB_ORIGIN,
        "Referer": f"{NOVELAI_WEB_ORIGIN}/",
        "sec-ch-ua": DEFAULT_SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "priority": "u=1, i",
    }
    if extra:
        headers.update(extra)
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

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        raise NotImplementedError
