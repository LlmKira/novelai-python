"""Tests marked ``network`` reach novelai.net (live API, tokenizer downloads); they are skipped offline."""

import functools
import os

import pytest


@functools.cache
def _novelai_reachable() -> bool:
    from curl_cffi import requests

    proxy = os.environ.get("NOVELAI_PROXY")
    try:
        with requests.Session(
            trust_env=False, proxies={"http": proxy, "https": proxy} if proxy else None, timeout=5
        ) as session:
            session.head("https://novelai.net/")
        return True
    except Exception:
        return False


def pytest_configure(config):
    config.addinivalue_line("markers", "network: needs novelai.net; skipped when it cannot be reached")


@pytest.hookimpl(trylast=True)  # after -m deselection: an offline run must not probe novelai.net
def pytest_collection_modifyitems(config, items):
    network_items = [item for item in items if "network" in item.keywords]
    if network_items and not _novelai_reachable():
        skip = pytest.mark.skip(reason="novelai.net is not reachable")
        for item in network_items:
            item.add_marker(skip)
