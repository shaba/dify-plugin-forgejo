from typing import Any
from urllib.parse import urlparse

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from forgejo_client.errors import redact_credentials
from forgejo_client.validate import validate


class ForgejoProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        base_url = str(credentials.get("base_url") or "").strip().rstrip("/")
        api_token = str(credentials.get("api_token") or "").strip() or None
        if not base_url:
            raise ToolProviderCredentialValidationError(
                "base_url is required (e.g. https://example.com)")
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ToolProviderCredentialValidationError(
                "base_url must be an http(s) URL with a host (e.g. https://example.com)")
        try:
            validate(base_url, api_token)
        except Exception as exc:  # noqa: BLE001
            raise ToolProviderCredentialValidationError(
                "Forgejo is not reachable or the token is invalid at "
                f"{redact_credentials(base_url)}: {redact_credentials(exc)}"
            ) from exc
