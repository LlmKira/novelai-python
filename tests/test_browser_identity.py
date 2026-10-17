import http.server
import threading

from curl_cffi import requests

from novelai_python.credential._base import IMPERSONATE, browser_headers, chrome_brands


def test_brand_list_matches_a_captured_chrome():
    # sec-ch-ua of a real Chrome 155 on novelai.net
    assert chrome_brands(155) == '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"'


def test_headers_describe_the_impersonated_browser():
    """User-Agent, sec-ch-ua and platform must be the ones curl_cffi's TLS profile belongs to."""
    seen: dict[str, str] = {}

    class Echo(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.update({k.lower(): v for k, v in self.headers.items()})
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Echo)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with requests.Session(impersonate=IMPERSONATE, trust_env=False) as session:
            session.get(f"http://127.0.0.1:{server.server_port}/")
    finally:
        server.shutdown()
    ours = browser_headers()
    for name in ("user-agent", "sec-ch-ua", "sec-ch-ua-platform", "accept-language"):
        assert ours[name] == seen[name], name
