from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import NotFound, redact_credentials
from forgejo_client.repos import format_user, get_authenticated_user, get_user
from tools._common import creds


class UserInfoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        username = str(tool_parameters.get("username") or "").strip()
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not username and not token:
            yield self.create_text_message(
                "Error: provide 'username', or configure an API token to view your own profile")
            return
        try:
            if username:
                user = get_user(base_url, username, token=token)
            else:
                user = get_authenticated_user(base_url, token=token)
        except NotFound as exc:
            yield self.create_text_message(redact_credentials(exc))
            return
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        yield self.create_text_message(format_user(user))
        yield self.create_json_message({
            "login": user.get("login"),
            "url": user.get("html_url"),
        })
