"""Check whether the browser identity in credential/_base.py is still current.

Two checks, both without third-party services:

1. Chrome version. Google's VersionHistory API lists the stable releases with the
   fraction of users each one is served to. The major version most users get is the one
   the headers should claim.
2. TLS (--tls). A local server reads the ClientHello of the Chrome installed on this machine
   and of curl_cffi's newest Chrome profile, and prints what differs: ciphers, extensions
   (sorted, Chrome permutes their order), groups, key shares, signature algorithms, ALPN.

usage:
  python scripts/refresh_browser_identity.py
  python scripts/refresh_browser_identity.py --tls [--chrome "C:/Program Files/Google/Chrome/Application/chrome.exe"]

The headers themselves (order, sec-fetch-*, priority) are best taken from a HAR of
novelai.net in a real browser.
"""

import argparse
import json
import os
import platform
import socket
import struct
import subprocess
import tempfile
import threading
from collections import defaultdict

from curl_cffi import requests

from novelai_python.credential._base import CHROME_MAJOR_VERSION, IMPERSONATE, chrome_brands

VERSION_API = (
    "https://versionhistory.googleapis.com/v1/chrome/platforms/{platform}/channels/stable/versions/all/releases"
    "?filter=endtime=none&pageSize=50"
)
GREASE = {0x0A0A + 0x1010 * i for i in range(16)}


def served_major(platform_name: str = "win") -> tuple[int, dict[int, float]]:
    """Major version served to most users now, and the served fraction per major."""
    with requests.Session(trust_env=False) as session:
        releases = session.get(VERSION_API.format(platform=platform_name), timeout=20).json().get("releases", [])
    share: dict[int, float] = defaultdict(float)
    for release in releases:
        # releases of one major overlap (rollout cohorts), so take the largest fraction, not the sum
        major = int(release["version"].split(".")[0])
        share[major] = max(share[major], float(release.get("fraction") or 0))
    return max(share, key=lambda major: share[major]), dict(share)


def _u16(b: bytes, o: int) -> int:
    return struct.unpack(">H", b[o : o + 2])[0]


def parse_client_hello(hello: bytes) -> dict:
    p = 9 + 2 + 32  # record + handshake headers, version, random
    p += 1 + hello[p]  # session id
    n = _u16(hello, p)
    ciphers = [c for c in (_u16(hello, p + 2 + i) for i in range(0, n, 2)) if c not in GREASE]
    p += 2 + n
    p += 1 + hello[p]  # compression methods
    end = p + 2 + _u16(hello, p)
    p += 2
    out: dict = {"ciphers": ciphers, "extensions": []}
    while p < end:
        kind, length = _u16(hello, p), _u16(hello, p + 2)
        body = hello[p + 4 : p + 4 + length]
        if kind not in GREASE:
            out["extensions"].append(kind)
        if kind == 10:
            out["groups"] = [g for g in (_u16(body, 2 + i) for i in range(0, _u16(body, 0), 2)) if g not in GREASE]
        elif kind == 13:
            out["sigalgs"] = [a for a in (_u16(body, 2 + i) for i in range(0, _u16(body, 0), 2)) if a not in GREASE]
        elif kind == 16:
            q, alpn = 2, []
            while q < len(body):
                alpn.append(body[q + 1 : q + 1 + body[q]].decode())
                q += 1 + body[q]
            out["alpn"] = alpn
        elif kind == 51:
            q, shares = 2, []
            while q < len(body):
                group, key_length = _u16(body, q), _u16(body, q + 2)
                if group not in GREASE:
                    shares.append(group)
                q += 4 + key_length
            out["key_shares"] = shares
        p += 4 + length
    out["extensions"].sort()
    return out


def capture(connect) -> dict:
    """Run ``connect(port)`` against a local socket and parse the first ClientHello it sends."""
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(30)
    port = server.getsockname()[1]
    threading.Thread(target=connect, args=(port,), daemon=True).start()
    conn, _ = server.accept()
    data = b""
    while len(data) < 5 or len(data) < 5 + _u16(data, 3):
        chunk = conn.recv(65536)
        if not chunk:
            break
        data += chunk
    conn.close()
    server.close()
    return parse_client_hello(data)


def _curl_cffi(port: int) -> None:
    try:
        with requests.Session(impersonate=IMPERSONATE, trust_env=False) as session:
            session.get(f"https://localhost:{port}/", timeout=5)
    except Exception:
        pass  # the local server never finishes the handshake


def _chrome(binary: str):
    def run(port: int) -> None:
        # Chrome may still hold files in the profile when it exits
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
            proc = subprocess.Popen(
                [binary, "--headless=new", "--no-proxy-server", "--no-first-run",
                 f"--user-data-dir={profile}", f"https://localhost:{port}/"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )  # fmt: skip
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    return run


def default_chrome() -> str:
    if platform.system() == "Windows":
        return os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe")
    if platform.system() == "Darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return "google-chrome"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tls", action="store_true", help="compare the local Chrome's ClientHello with curl_cffi")
    parser.add_argument("--chrome", default=default_chrome(), help="path to the Chrome binary")
    args = parser.parse_args()

    major, share = served_major()
    print(f"stable Chrome served now: {major}  (largest served fraction per major: {share})")
    print(f"library claims:           {CHROME_MAJOR_VERSION}")
    if str(major) != CHROME_MAJOR_VERSION:
        print(f'-> set CHROME_MAJOR_VERSION = "{major}"; sec-ch-ua becomes {chrome_brands(major)}')
    else:
        print("-> up to date")

    if args.tls:
        ours = capture(_curl_cffi)
        real = capture(_chrome(args.chrome))
        print(f"\nTLS: local Chrome vs curl_cffi {IMPERSONATE}")
        same = True
        for key in sorted(set(ours) | set(real)):
            a, b = real.get(key), ours.get(key)
            if a == b:
                continue
            same = False
            if isinstance(a, list) and isinstance(b, list):
                print(f"  {key}: only in Chrome {sorted(set(a) - set(b))}, only in curl_cffi {sorted(set(b) - set(a))}")
                if sorted(a) == sorted(b):
                    print(f"  {key}: same values, different order")
            else:
                print(f"  {key}: Chrome {a} / curl_cffi {b}")
        print("  identical" if same else "")
        print(json.dumps({"chrome": real, "curl_cffi": ours}))


if __name__ == "__main__":
    main()
