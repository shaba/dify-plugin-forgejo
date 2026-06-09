import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def static_fetch(payload, status: int = 200):
    """Return a Fetch callable that always yields (status, payload)."""
    def f(method, url, *, token=None, json_body=None, timeout=30):
        return status, payload
    return f


def capturing_fetch(status: int, payload):
    """Fetch that records the last call for assertions on write tools."""
    calls = []

    def f(method, url, *, token=None, json_body=None, timeout=30):
        calls.append({"method": method, "url": url, "token": token,
                      "json_body": json_body})
        return status, payload

    f.calls = calls
    return f


@pytest.fixture
def fixtures():
    return load_fixture


@pytest.fixture
def make_static():
    return static_fetch


@pytest.fixture
def make_capturing():
    return capturing_fetch
