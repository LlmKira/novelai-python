import pytest

from novelai_python import ApiCredential
from novelai_python.credential._base import (
    ACCEPT_LANGUAGES,
    CHROME_MAJOR_VERSION,
    browser_headers,
    chrome_brands,
    resolve_accept_language,
)


@pytest.mark.parametrize(
    ("major", "captured"),
    [
        # a real Chrome 155 on novelai.net (HAR)
        (155, '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"'),
        # what curl_cffi's chrome150 profile sends
        (150, '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"'),
    ],
)
def test_brand_list_matches_captured_chrome(major, captured):
    assert chrome_brands(major) == captured


def test_headers_match_the_captured_web_client():
    # request headers of /ai/generate-image from Chrome 155 on Windows (HAR), language aside
    captured = {
        "accept": "*/*",
        "origin": "https://novelai.net",
        "referer": "https://novelai.net/",
        "sec-ch-ua": '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/155.0.0.0 Safari/537.36"
        ),
    }
    headers = browser_headers()
    assert {k: headers[k] for k in captured} == captured
    assert headers["accept-language"] == "en-US,en;q=0.9"
    assert CHROME_MAJOR_VERSION == "155"


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
