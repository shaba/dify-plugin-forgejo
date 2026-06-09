from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import redact_credentials
from forgejo_client.issues import create_issue
from tools._common import creds


class CreateIssueTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        owner = str(tool_parameters.get("owner") or "").strip()
        repo = str(tool_parameters.get("repo") or "").strip()
        title = str(tool_parameters.get("title") or "").strip()
        body = str(tool_parameters.get("body") or "").strip() or None
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not token:
            yield self.create_text_message("Error: an API token is required to create an issue")
            return
        if not owner or not repo or not title:
            yield self.create_text_message("Error: 'owner', 'repo' and 'title' are required")
            return
        try:
            issue = create_issue(base_url, owner, repo, title, body=body, token=token)
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        num = issue.get("number")
        url = issue.get("html_url")
        yield self.create_text_message(
            f"Created issue #{num} in {owner}/{repo}: {title}\nLink: {url}")
        yield self.create_json_message({
            "number": num, "title": issue.get("title"), "url": url,
        })
