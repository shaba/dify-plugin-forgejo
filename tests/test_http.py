import pytest

from forgejo_client.errors import ApiError, NotFound, redact_credentials
from forgejo_client.http import (
    api_base,
    build_url,
    default_fetch,
    request,
    seg,
    seg_path,
)


def test_api_base_and_build_url():
    assert api_base("https://example.com/") == "https://example.com/api/v1"
    url = build_url("https://example.com", "repos/search", {"q": "x", "limit": 5})
    assert url == "https://example.com/api/v1/repos/search?q=x&limit=5"


def test_build_url_drops_empty_params():
    url = build_url("https://example.com", "user/repos", {"limit": 5, "ref": None, "q": ""})
    assert url == "https://example.com/api/v1/user/repos?limit=5"


def test_seg_quotes_segment():
    assert seg("a/b") == "a%2Fb"


def test_seg_path_keeps_separators_but_encodes_components():
    assert seg_path("docs/with space/a?b#c.md") == "docs/with%20space/a%3Fb%23c.md"
    assert seg_path("/leading/trailing/") == "leading/trailing"
    assert seg_path("") == ""


def test_request_raises_not_found():
    def f(method, url, *, token=None, json_body=None, timeout=30):
        return 404, {"message": "nope"}
    with pytest.raises(NotFound):
        request("https://example.com", "GET", "repos/x/y", fetch=f)


def test_request_raises_api_error():
    def f(method, url, *, token=None, json_body=None, timeout=30):
        return 500, {"message": "boom"}
    with pytest.raises(ApiError):
        request("https://example.com", "GET", "repos/x/y", fetch=f)


def test_redact_credentials_strips_userinfo():
    msg = "Forgejo API request failed for https://user:secret@git.example.com/api/v1/user"
    redacted = redact_credentials(msg)
    assert "secret" not in redacted
    assert "user:secret@" not in redacted
    assert "https://git.example.com" in redacted


def test_request_redacts_userinfo_in_error_at_source():
    def f(method, url, *, token=None, json_body=None, timeout=30):
        # Server echoes the full URL (with credentials) back in the error body.
        return 500, {"message": "boom at https://user:pass@git.example.com/api/v1/x"}

    with pytest.raises(ApiError) as excinfo:
        request("https://user:pass@git.example.com", "GET", "repos/x/y", fetch=f)
    text = str(excinfo.value)
    assert "user:pass@" not in text
    assert "pass" not in text


def test_default_fetch_rejects_non_http_scheme():
    with pytest.raises(ApiError) as excinfo:
        default_fetch("GET", "file:///etc/passwd")
    assert "scheme" in str(excinfo.value).lower()


def test_default_fetch_normalizes_transport_error_and_redacts(monkeypatch):
    import forgejo_client.http as http

    def boom(*a, **k):
        raise http.requests.ConnectionError(
            "failed to connect to https://user:secret@git.example.com")

    monkeypatch.setattr(http.requests, "request", boom)
    with pytest.raises(ApiError) as excinfo:
        http.default_fetch("GET", "https://user:secret@git.example.com/api/v1/user")
    text = str(excinfo.value)
    assert "secret" not in text
    assert "user:secret@" not in text


def test_default_fetch_builds_auth_header_and_decodes(monkeypatch):
    import forgejo_client.http as http

    seen = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"ok": True}

        @property
        def text(self):
            return '{"ok": true}'

    def fake_request(method, url, *, headers=None, json=None, timeout=None,
                     allow_redirects=None):
        seen.update(method=method, url=url, headers=headers, json=json,
                    timeout=timeout, allow_redirects=allow_redirects)
        return FakeResponse()

    monkeypatch.setattr(http.requests, "request", fake_request)
    status, data = http.default_fetch("GET", "https://example.com/api/v1/user", token="abc")
    assert status == 200
    assert data == {"ok": True}
    assert seen["headers"]["Authorization"] == "token abc"
    assert seen["headers"]["Accept"] == "application/json"
    assert seen["allow_redirects"] is False
    assert seen["timeout"] == 30


def test_default_fetch_falls_back_to_text_on_non_json(monkeypatch):
    import forgejo_client.http as http

    class FakeResponse:
        status_code = 200

        def json(self):
            raise ValueError("not json")

        @property
        def text(self):
            return "plain body"

    monkeypatch.setattr(http.requests, "request",
                        lambda *a, **k: FakeResponse())
    status, data = http.default_fetch("GET", "https://example.com/api/v1/x")
    assert status == 200
    assert data == "plain body"


def test_request_passes_token_and_body():
    seen = {}

    def f(method, url, *, token=None, json_body=None, timeout=30):
        seen.update(method=method, token=token, json_body=json_body)
        return 200, {"ok": True}

    out = request("https://example.com", "POST", "repos/x/y/issues",
                  token="t", json_body={"title": "hi"}, fetch=f)
    assert out == {"ok": True}
    assert seen == {"method": "POST", "token": "t", "json_body": {"title": "hi"}}
