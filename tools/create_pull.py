from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import redact_credentials
from forgejo_client.issues import create_pull
from tools._common import creds


class CreatePullTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        owner = str(tool_parameters.get("owner") or "").strip()
        repo = str(tool_parameters.get("repo") or "").strip()
        head = str(tool_parameters.get("head") or "").strip()
        base = str(tool_parameters.get("base") or "").strip()
        title = str(tool_parameters.get("title") or "").strip()
        body = str(tool_parameters.get("body") or "").strip() or None
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not token:
            yield self.create_text_message(
                "Error: an API token is required to create a pull request")
            return
        if not owner or not repo or not head or not base or not title:
            yield self.create_text_message(
                "Error: 'owner', 'repo', 'head', 'base' and 'title' are required")
            return
        try:
            pull = create_pull(base_url, owner, repo, head=head, base=base,
                               title=title, body=body, token=token)
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        num = pull.get("number")
        url = pull.get("html_url")
        yield self.create_text_message(
            f"Created pull request #{num} in {owner}/{repo}: {head} -> {base}\n"
            f"{title}\nLink: {url}")
        yield self.create_json_message({
            "number": num, "title": pull.get("title"), "url": url,
        })
