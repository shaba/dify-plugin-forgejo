from typing import Any


def creds(runtime: Any) -> tuple[str, str | None]:
    """Return (base_url, api_token) from the tool runtime credentials."""
    c = runtime.credentials or {}
    base_url = str(c.get("base_url") or "").strip().rstrip("/")
    api_token = str(c.get("api_token") or "").strip() or None
    return base_url, api_token


def parse_index(value: Any) -> int | None:
    """Coerce an issue/PR number to a positive int, or None if invalid.

    Dify 'number' parameters may arrive as int, float (e.g. 5.0) or a numeric
    string, so accept any of those rather than gating on str.isdigit().
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        index = int(float(text))
    except (TypeError, ValueError):
        return None
    return index if index > 0 else None
