from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import redact_credentials
from forgejo_client.repos import format_repo_list, list_repos
from tools._common import creds


class ListReposTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        username = str(tool_parameters.get("username") or "").strip() or None
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not username and not token:
            yield self.create_text_message(
                "Error: provide 'username', or configure an API token to list your own repos")
            return
        try:
            repos = list_repos(base_url, username, limit=30, token=token)
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        heading = f"Repositories of {username}" if username else "Your repositories"
        yield self.create_text_message(format_repo_list(repos, heading))
        yield self.create_json_message({"username": username, "count": len(repos)})
