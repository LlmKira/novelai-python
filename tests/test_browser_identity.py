import pytest

from novelai_python import ApiCredential
from novelai_python.credential._base import (
    ACCEPT_LANGUAGES,
    CHROME_MAJOR_VERSION,
    browser_headers,
    chrome_brands,
    resolve_accept_language,
)


def test_brand_list_matches_a_captured_chrome():
    # sec-ch-ua of a real Chrome 155 on novelai.net
    assert chrome_brands(155) == '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"'


def test_headers_describe_one_browser():
    headers = browser_headers()
    assert f"Chrome/{CHROME_MAJOR_VERSION}.0.0.0" in headers["user-agent"]
    assert headers["sec-ch-ua"] == chrome_brands(int(CHROME_MAJOR_VERSION))
    assert "Windows NT" in headers["user-agent"] and headers["sec-ch-ua-platform"] == '"Windows"'
    assert headers["accept-language"] == "en-US,en;q=0.9"


def test_accept_language_presets():
    assert resolve_accept_language(None) == "en-US,en;q=0.9"
    assert resolve_accept_language("en-SG") == ACCEPT_LANGUAGES["en-sg"] == "en-SG,en;q=0.9"
    assert resolve_accept_language("de-DE,de;q=0.9") == "de-DE,de;q=0.9"


@pytest.mark.asyncio
async def test_credential_sends_its_language():
    session = await ApiCredential(api_token="pst-a", accept_language="en-sg").get_session()
    assert session.headers["accept-language"] == "en-SG,en;q=0.9"
    await session.close()
    session = await ApiCredential(api_token="pst-a").get_session()
    assert session.headers["accept-language"] == "en-US,en;q=0.9"
    await session.close()
