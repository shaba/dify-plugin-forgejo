from __future__ import annotations

from typing import Any

from .http import Fetch, default_fetch, request, seg


def _repo_path(owner: str, repo: str) -> str:
    return f"repos/{seg(owner)}/{seg(repo)}"


# --- read -----------------------------------------------------------------
# The list_* helpers fetch a single page ('limit' only, no 'page'). Forgejo
# caps a response at the server's max page size (default 50), so 'limit' is
# honoured only up to that cap; larger values are silently truncated.

def list_issues(base_url: str, owner: str, repo: str, *, state: str = "open",
                query: str | None = None, labels: str | None = None, limit: int = 20,
                token: str | None = None, fetch: Fetch = default_fetch,
                timeout: int = 30) -> list[dict[str, Any]]:
    data = request(base_url, "GET", f"{_repo_path(owner, repo)}/issues",
                   params={"state": state, "q": query, "labels": labels,
                           "type": "issues", "limit": limit},
                   token=token, fetch=fetch, timeout=timeout)
    return [i for i in (data or []) if isinstance(i, dict)]


def get_issue(base_url: str, owner: str, repo: str, index: int, *,
              token: str | None = None, fetch: Fetch = default_fetch,
              timeout: int = 30) -> dict[str, Any]:
    return request(base_url, "GET", f"{_repo_path(owner, repo)}/issues/{int(index)}",
                   token=token, fetch=fetch, timeout=timeout)


def get_issue_comments(base_url: str, owner: str, repo: str, index: int, *,
                       token: str | None = None, fetch: Fetch = default_fetch,
                       timeout: int = 30) -> list[dict[str, Any]]:
    data = request(base_url, "GET",
                   f"{_repo_path(owner, repo)}/issues/{int(index)}/comments",
                   token=token, fetch=fetch, timeout=timeout)
    return [c for c in (data or []) if isinstance(c, dict)]


def list_pulls(base_url: str, owner: str, repo: str, *, state: str = "open",
               limit: int = 20, token: str | None = None,
               fetch: Fetch = default_fetch, timeout: int = 30) -> list[dict[str, Any]]:
    data = request(base_url, "GET", f"{_repo_path(owner, repo)}/pulls",
                   params={"state": state, "limit": limit}, token=token,
                   fetch=fetch, timeout=timeout)
    return [p for p in (data or []) if isinstance(p, dict)]


def get_pull(base_url: str, owner: str, repo: str, index: int, *,
             token: str | None = None, fetch: Fetch = default_fetch,
             timeout: int = 30) -> dict[str, Any]:
    return request(base_url, "GET", f"{_repo_path(owner, repo)}/pulls/{int(index)}",
                   token=token, fetch=fetch, timeout=timeout)


# --- write ----------------------------------------------------------------

def create_issue(base_url: str, owner: str, repo: str, title: str, *,
                 body: str | None = None, token: str | None = None,
                 fetch: Fetch = default_fetch, timeout: int = 30) -> dict[str, Any]:
    payload: dict[str, Any] = {"title": title}
    if body:
        payload["body"] = body
    return request(base_url, "POST", f"{_repo_path(owner, repo)}/issues",
                   json_body=payload, token=token, fetch=fetch, timeout=timeout)


def create_comment(base_url: str, owner: str, repo: str, index: int, body: str, *,
                   token: str | None = None, fetch: Fetch = default_fetch,
                   timeout: int = 30) -> dict[str, Any]:
    """Comment on an issue or a pull request (same endpoint in Forgejo/Gitea)."""
    return request(base_url, "POST",
                   f"{_repo_path(owner, repo)}/issues/{int(index)}/comments",
                   json_body={"body": body}, token=token, fetch=fetch, timeout=timeout)


def create_pull(base_url: str, owner: str, repo: str, *, head: str, base: str,
                title: str, body: str | None = None, token: str | None = None,
                fetch: Fetch = default_fetch, timeout: int = 30) -> dict[str, Any]:
    payload: dict[str, Any] = {"head": head, "base": base, "title": title}
    if body:
        payload["body"] = body
    return request(base_url, "POST", f"{_repo_path(owner, repo)}/pulls",
                   json_body=payload, token=token, fetch=fetch, timeout=timeout)


def merge_pull(base_url: str, owner: str, repo: str, index: int, *,
               do: str = "merge", title: str | None = None, message: str | None = None,
               token: str | None = None, fetch: Fetch = default_fetch,
               timeout: int = 30) -> dict[str, Any]:
    # Keys match Gitea/Forgejo's MergePullRequestOption JSON schema (snake_case).
    payload: dict[str, Any] = {"do": do}
    if title:
        payload["merge_title_field"] = title
    if message:
        payload["merge_message_field"] = message
    # Forgejo returns 200 with empty body on success; request() raises on >=400.
    return request(base_url, "POST",
                   f"{_repo_path(owner, repo)}/pulls/{int(index)}/merge",
                   json_body=payload, token=token, fetch=fetch, timeout=timeout)


# --- formatting -----------------------------------------------------------

def _state_tag(item: dict[str, Any]) -> str:
    state = str(item.get("state") or "").strip()
    if item.get("merged"):
        return "merged"
    return state or "?"


def format_issue_list(issues: list[dict[str, Any]], owner: str, repo: str,
                      *, kind: str = "issues") -> str:
    if not issues:
        return f"No {kind} found in {owner}/{repo}."
    lines = [f"{kind.capitalize()} in {owner}/{repo} ({len(issues)}):"]
    for i in issues:
        num = i.get("number")
        title = str(i.get("title") or "").strip()
        state = _state_tag(i)
        author = (i.get("user") or {}).get("login") or ""
        lines.append(f"- #{num} [{state}] {title} (by {author})")
    return "\n".join(lines)


def format_issue(issue: dict[str, Any], comments: list[dict[str, Any]], *,
                 owner: str, repo: str, max_comments: int = 5,
                 comment_lines: int = 4) -> str:
    num = issue.get("number")
    title = str(issue.get("title") or "").strip()
    state = _state_tag(issue)
    author = (issue.get("user") or {}).get("login") or ""
    lines = [f"#{num} [{state}] {title}"]
    meta = [f"author: {author}"]
    labels = [str((label_obj.get("name") or "")).strip()
              for label_obj in (issue.get("labels") or []) if isinstance(label_obj, dict)]
    labels = [label for label in labels if label]
    if labels:
        meta.append(f"labels: {', '.join(labels)}")
    assignees = [str((a.get("login") or "")).strip()
                 for a in (issue.get("assignees") or []) if isinstance(a, dict)]
    assignees = [a for a in assignees if a]
    if assignees:
        meta.append(f"assignees: {', '.join(assignees)}")
    lines.append(", ".join(meta))

    body = _first_lines(issue.get("body") or "", 8)
    if body:
        lines.append("")
        lines.append(body)

    if issue.get("html_url"):
        lines.append(f"Link: {issue.get('html_url')}")

    if comments:
        shown = min(len(comments), max_comments)
        if len(comments) > max_comments:
            header = f"Comments (showing first {shown} of {len(comments)} fetched):"
        else:
            header = f"Comments ({len(comments)}):"
        lines.append("")
        lines.append(header)
        for c in comments[:max_comments]:
            who = (c.get("user") or {}).get("login") or ""
            when = str(c.get("created_at") or "")[:10]
            text = _first_lines(c.get("body") or "", comment_lines)
            lines.append(f"{who} {when}:")
            if text:
                lines.append(text)
    return "\n".join(lines).strip()


def format_pull(pull: dict[str, Any], *, owner: str, repo: str) -> str:
    num = pull.get("number")
    title = str(pull.get("title") or "").strip()
    state = _state_tag(pull)
    author = (pull.get("user") or {}).get("login") or ""
    base = (pull.get("base") or {}).get("label") or (pull.get("base") or {}).get("ref") or ""
    head = (pull.get("head") or {}).get("label") or (pull.get("head") or {}).get("ref") or ""
    lines = [f"PR #{num} [{state}] {title}"]
    lines.append(f"author: {author}, {head} -> {base}")
    if pull.get("mergeable") is not None and not pull.get("merged"):
        lines.append(f"mergeable: {pull.get('mergeable')}")
    body = _first_lines(pull.get("body") or "", 8)
    if body:
        lines.append("")
        lines.append(body)
    if pull.get("html_url"):
        lines.append(f"Link: {pull.get('html_url')}")
    return "\n".join(lines).strip()


def _first_lines(text: str, count: int) -> str:
    lines = [" ".join(line.split()) for line in str(text).splitlines() if line.strip()]
    return "\n".join(lines[:count])
