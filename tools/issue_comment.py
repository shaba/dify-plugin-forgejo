from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import redact_credentials
from forgejo_client.issues import create_comment
from tools._common import creds, parse_index


class IssueCommentTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        owner = str(tool_parameters.get("owner") or "").strip()
        repo = str(tool_parameters.get("repo") or "").strip()
        index = parse_index(tool_parameters.get("index"))
        body = str(tool_parameters.get("body") or "").strip()
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not token:
            yield self.create_text_message("Error: an API token is required to post a comment")
            return
        if not owner or not repo or index is None or not body:
            yield self.create_text_message(
                "Error: 'owner', 'repo', a numeric 'index' and 'body' are required")
            return
        try:
            comment = create_comment(base_url, owner, repo, index, body, token=token)
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        url = comment.get("html_url")
        yield self.create_text_message(
            f"Posted comment on {owner}/{repo}#{index}.\nLink: {url}")
        yield self.create_json_message({
            "id": comment.get("id"), "index": int(index), "url": url,
        })
