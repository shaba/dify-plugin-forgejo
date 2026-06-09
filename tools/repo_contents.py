from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import NotFound, redact_credentials
from forgejo_client.repos import format_contents, get_contents
from tools._common import creds


class RepoContentsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        owner = str(tool_parameters.get("owner") or "").strip()
        repo = str(tool_parameters.get("repo") or "").strip()
        path = str(tool_parameters.get("path") or "").strip()
        ref = str(tool_parameters.get("ref") or "").strip() or None
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not owner or not repo:
            yield self.create_text_message("Error: 'owner' and 'repo' are required")
            return
        try:
            data = get_contents(base_url, owner, repo, path, ref=ref, token=token)
        except NotFound as exc:
            yield self.create_text_message(redact_credentials(exc))
            return
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        yield self.create_text_message(format_contents(data, owner, repo, path))
        is_dir = isinstance(data, list)
        yield self.create_json_message({
            "owner": owner, "repo": repo, "path": path,
            "type": "dir" if is_dir else "file",
            "entries": len(data) if is_dir else 1,
        })
