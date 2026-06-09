from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import redact_credentials
from forgejo_client.repos import format_repo_list, search_repos
from tools._common import creds


class SearchReposTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        query = str(tool_parameters.get("query") or "").strip()
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not query:
            yield self.create_text_message("Error: the 'query' parameter is required")
            return
        try:
            repos = search_repos(base_url, query, limit=20, token=token)
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        yield self.create_text_message(
            format_repo_list(repos, f"Repositories matching \"{query}\""))
        yield self.create_json_message({"query": query, "count": len(repos)})
