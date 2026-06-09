from __future__ import annotations

from .errors import ApiError, ForgejoError, redact_credentials
from .http import Fetch, default_fetch
from .repos import get_authenticated_user, get_version


def validate(base_url: str, token: str | None, *,
             fetch: Fetch = default_fetch, timeout: int = 15) -> None:
    """Validate connectivity and credentials.

    If a token is given, verify it via /api/v1/user. Otherwise just check that the
    server speaks the Forgejo/Gitea API via /api/v1/version. Raises ``ForgejoError``
    on failure with any embedded ``user:pass@`` redacted.
    """
    try:
        if token:
            get_authenticated_user(base_url, token=token, fetch=fetch, timeout=timeout)
        else:
            get_version(base_url, fetch=fetch, timeout=timeout)
    except ForgejoError as exc:
        raise ApiError(redact_credentials(exc)) from exc
    except Exception as exc:  # noqa: BLE001  (transport errors etc.)
        raise ApiError(redact_credentials(exc)) from exc
