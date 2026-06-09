import pytest

from forgejo_client.errors import ApiError
from forgejo_client.validate import validate


def test_validate_with_token_calls_user():
    seen = {}

    def f(method, url, *, token=None, json_body=None, timeout=30):
        seen["url"] = url
        return 200, {"login": "alice"}

    validate("https://example.com", "t", fetch=f)
    assert seen["url"].endswith("/api/v1/user")


def test_validate_without_token_calls_version():
    seen = {}

    def f(method, url, *, token=None, json_body=None, timeout=30):
        seen["url"] = url
        return 200, {"version": "1.0"}

    validate("https://example.com", None, fetch=f)
    assert seen["url"].endswith("/api/v1/version")


def test_validate_raises_on_bad_token(make_static):
    with pytest.raises(ApiError):
        validate("https://example.com", "bad", fetch=make_static({"message": "unauth"}, 401))


def test_validate_redacts_credentials_in_error(make_static):
    # A base_url with embedded user:pass@ must not leak into the error text the
    # provider surfaces to the user/LLM.
    with pytest.raises(ApiError) as excinfo:
        validate("https://user:secret@git.example.com", "bad",
                 fetch=make_static({"message": "error at "
                                    "https://user:secret@git.example.com/api/v1/user"}, 401))
    text = str(excinfo.value)
    assert "secret" not in text
    assert "user:secret@" not in text
