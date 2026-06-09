from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from forgejo_client.errors import NotFound, redact_credentials
from forgejo_client.repos import format_commits, list_commits
from tools._common import creds


class RepoCommitsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url, token = creds(self.runtime)
        owner = str(tool_parameters.get("owner") or "").strip()
        repo = str(tool_parameters.get("repo") or "").strip()
        sha = str(tool_parameters.get("ref") or "").strip() or None
        if not base_url:
            yield self.create_text_message("Error: the plugin base_url is not configured")
            return
        if not owner or not repo:
            yield self.create_text_message("Error: 'owner' and 'repo' are required")
            return
        try:
            commits = list_commits(base_url, owner, repo, sha=sha, limit=20, token=token)
        except NotFound as exc:
            yield self.create_text_message(redact_credentials(exc))
            return
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"Forgejo request error: {redact_credentials(exc)}")
            return
        yield self.create_text_message(format_commits(commits, owner, repo))
        yield self.create_json_message({"owner": owner, "repo": repo, "count": len(commits)})
