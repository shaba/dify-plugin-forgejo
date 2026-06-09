from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import NotFound, redact_credentials
from forgejo_client.issues import format_pull, get_pull
from tools._common import creds, parse_index


class GetPullTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        owner = str(tool_parameters.get("owner") or "").strip()
        repo = str(tool_parameters.get("repo") or "").strip()
        index = parse_index(tool_parameters.get("index"))
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not owner or not repo or index is None:
            yield self.create_text_message(
                "Error: 'owner', 'repo' and a numeric 'index' are required")
            return
        try:
            pull = get_pull(base_url, owner, repo, index, token=token)
        except NotFound as exc:
            yield self.create_text_message(redact_credentials(exc))
            return
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        yield self.create_text_message(format_pull(pull, owner=owner, repo=repo))
        yield self.create_json_message({
            "number": pull.get("number"),
            "state": pull.get("state"),
            "merged": pull.get("merged"),
            "title": pull.get("title"),
            "url": pull.get("html_url"),
        })
