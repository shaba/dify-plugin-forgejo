from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import redact_credentials
from forgejo_client.issues import merge_pull
from tools._common import creds, parse_index

VALID_METHODS = ("merge", "rebase", "rebase-merge", "squash")


class MergePullTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        owner = str(tool_parameters.get("owner") or "").strip()
        repo = str(tool_parameters.get("repo") or "").strip()
        index = parse_index(tool_parameters.get("index"))
        do = str(tool_parameters.get("merge_method") or "merge").strip() or "merge"
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not token:
            yield self.create_text_message(
                "Error: an API token is required to merge a pull request")
            return
        if not owner or not repo or index is None:
            yield self.create_text_message(
                "Error: 'owner', 'repo' and a numeric 'index' are required")
            return
        if do not in VALID_METHODS:
            yield self.create_text_message(
                f"Error: 'merge_method' must be one of: {', '.join(VALID_METHODS)}")
            return
        try:
            merge_pull(base_url, owner, repo, index, do=do, token=token)
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        # Forgejo may queue the merge (async); a 2xx means the request was accepted.
        yield self.create_text_message(
            f"Requested merge of pull request {owner}/{repo}#{index} using '{do}'.")
        yield self.create_json_message({
            "owner": owner, "repo": repo, "index": index,
            "merge_method": do, "merge_requested": True,
        })
