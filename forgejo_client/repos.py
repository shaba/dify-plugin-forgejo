from __future__ import annotations

import base64
from typing import Any

from .errors import NotFound
from .http import Fetch, default_fetch, request, seg, seg_path

# Ordered preference for README detection in the repo root listing.
README_NAMES = (
    "README.md",
    "readme.md",
    "Readme.md",
    "README.rst",
    "README.txt",
    "README",
)


def get_version(base_url: str, *, token: str | None = None,
                fetch: Fetch = default_fetch, timeout: int = 30) -> dict[str, Any]:
    return request(base_url, "GET", "version", token=token, fetch=fetch, timeout=timeout)


def get_authenticated_user(base_url: str, *, token: str | None = None,
                           fetch: Fetch = default_fetch, timeout: int = 30) -> dict[str, Any]:
    return request(base_url, "GET", "user", token=token, fetch=fetch, timeout=timeout)


def get_user(base_url: str, username: str, *, token: str | None = None,
             fetch: Fetch = default_fetch, timeout: int = 30) -> dict[str, Any]:
    return request(base_url, "GET", f"users/{seg(username)}", token=token,
                   fetch=fetch, timeout=timeout)


def get_repo(base_url: str, owner: str, repo: str, *, token: str | None = None,
             fetch: Fetch = default_fetch, timeout: int = 30) -> dict[str, Any]:
    return request(base_url, "GET", f"repos/{seg(owner)}/{seg(repo)}", token=token,
                   fetch=fetch, timeout=timeout)


def list_repos(base_url: str, username: str | None = None, *, limit: int = 30,
               token: str | None = None, fetch: Fetch = default_fetch,
               timeout: int = 30) -> list[dict[str, Any]]:
    """Repos of `username` (user or org); if username is empty, the token user's repos."""
    if username:
        path = f"users/{seg(username)}/repos"
    else:
        path = "user/repos"
    data = request(base_url, "GET", path, params={"limit": limit}, token=token,
                   fetch=fetch, timeout=timeout)
    return [r for r in (data or []) if isinstance(r, dict)]


def search_repos(base_url: str, query: str, *, limit: int = 20, token: str | None = None,
                 fetch: Fetch = default_fetch, timeout: int = 30) -> list[dict[str, Any]]:
    data = request(base_url, "GET", "repos/search", params={"q": query, "limit": limit},
                   token=token, fetch=fetch, timeout=timeout)
    if isinstance(data, dict):
        data = data.get("data") or []
    return [r for r in (data or []) if isinstance(r, dict)]


def get_contents(base_url: str, owner: str, repo: str, path: str = "", *,
                 ref: str | None = None, token: str | None = None,
                 fetch: Fetch = default_fetch, timeout: int = 30) -> Any:
    api_path = f"repos/{seg(owner)}/{seg(repo)}/contents"
    encoded = seg_path(path)
    if encoded:
        api_path = f"{api_path}/{encoded}"
    return request(base_url, "GET", api_path, params={"ref": ref}, token=token,
                   fetch=fetch, timeout=timeout)


def find_readme_entry(listing: Any) -> dict[str, Any] | None:
    """Pick a README entry from a repo-root directory listing, or None."""
    if not isinstance(listing, list):
        return None
    by_name = {str(e.get("name") or ""): e for e in listing if isinstance(e, dict)}
    for name in README_NAMES:
        if name in by_name:
            return by_name[name]
    for name, entry in by_name.items():
        if name.lower().startswith("readme"):
            return entry
    return None


def get_readme(base_url: str, owner: str, repo: str, *, ref: str | None = None,
               token: str | None = None, fetch: Fetch = default_fetch,
               timeout: int = 30) -> dict[str, Any]:
    """Gitea/Forgejo has no dedicated README endpoint: list root, find a README file."""
    listing = get_contents(base_url, owner, repo, "", ref=ref, token=token,
                            fetch=fetch, timeout=timeout)
    if not isinstance(listing, list):
        raise NotFound("Repository root is not a directory listing")
    readme_entry = find_readme_entry(listing)
    if readme_entry is None:
        raise NotFound(f"No README found in {owner}/{repo}")
    return get_contents(base_url, owner, repo, str(readme_entry.get("path") or ""),
                        ref=ref, token=token, fetch=fetch, timeout=timeout)


def list_commits(base_url: str, owner: str, repo: str, *, sha: str | None = None,
                 path: str | None = None, limit: int = 20, token: str | None = None,
                 fetch: Fetch = default_fetch, timeout: int = 30) -> list[dict[str, Any]]:
    data = request(base_url, "GET", f"repos/{seg(owner)}/{seg(repo)}/commits",
                   params={"sha": sha, "path": path, "limit": limit}, token=token,
                   fetch=fetch, timeout=timeout)
    return [c for c in (data or []) if isinstance(c, dict)]


def list_releases(base_url: str, owner: str, repo: str, *, limit: int = 20,
                  token: str | None = None, fetch: Fetch = default_fetch,
                  timeout: int = 30) -> list[dict[str, Any]]:
    data = request(base_url, "GET", f"repos/{seg(owner)}/{seg(repo)}/releases",
                   params={"limit": limit}, token=token, fetch=fetch, timeout=timeout)
    return [r for r in (data or []) if isinstance(r, dict)]


def decode_file_content(entry: dict[str, Any]) -> str | None:
    """Decode a base64 ``content`` field from a contents file entry.

    Returns ``None`` when the entry carries no decodable content (binary/large
    files come without a ``content`` field, so the caller can fall back to the
    download URL). A genuinely *empty* file has ``content == ""`` (a present but
    empty field), which decodes to ``""`` — distinct from absent content.
    """
    content = entry.get("content")
    if entry.get("encoding") == "base64" and content is not None:
        try:
            return base64.b64decode(content).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            return None
    return None


# --- formatting -----------------------------------------------------------

def format_repo(repo: dict[str, Any]) -> str:
    full = repo.get("full_name") or repo.get("name") or "?"
    lines = [f"Repository {full}"]
    desc = str(repo.get("description") or "").strip()
    if desc:
        lines.append(desc)
    meta = []
    lang = str(repo.get("language") or "").strip()
    if lang:
        meta.append(f"language: {lang}")
    meta.append(f"stars: {repo.get('stars_count', 0)}")
    meta.append(f"forks: {repo.get('forks_count', 0)}")
    meta.append(f"open issues: {repo.get('open_issues_count', 0)}")
    if repo.get("private"):
        meta.append("private")
    if repo.get("archived"):
        meta.append("archived")
    lines.append(", ".join(meta))
    branch = str(repo.get("default_branch") or "").strip()
    if branch:
        lines.append(f"Default branch: {branch}")
    if repo.get("html_url"):
        lines.append(f"Link: {repo.get('html_url')}")
    return "\n".join(lines)


def format_repo_list(repos: list[dict[str, Any]], heading: str) -> str:
    if not repos:
        return f"{heading}: none found."
    lines = [f"{heading} ({len(repos)}):"]
    for r in repos:
        full = r.get("full_name") or r.get("name") or "?"
        desc = str(r.get("description") or "").strip()
        stars = r.get("stars_count", 0)
        line = f"- {full} (★{stars})"
        if desc:
            line += f": {desc}"
        lines.append(line)
    return "\n".join(lines)


def format_contents(contents: Any, owner: str, repo: str, path: str) -> str:
    where = f"{owner}/{repo}/{path}".rstrip("/")
    if isinstance(contents, list):
        if not contents:
            return f"{where}: empty directory."
        lines = [f"Directory {where} ({len(contents)} entries):"]
        for e in contents:
            if not isinstance(e, dict):
                continue
            kind = "dir" if e.get("type") == "dir" else "file"
            size = e.get("size")
            name = e.get("name")
            line = f"- [{kind}] {name}"
            if kind == "file" and size is not None:
                line += f" ({size} bytes)"
            lines.append(line)
        return "\n".join(lines)
    if isinstance(contents, dict):
        text = decode_file_content(contents)
        size = contents.get("size")
        header = f"File {where}" if size is None else f"File {where} ({size} bytes)"
        lines = [f"{header}:"]
        if text is not None:
            all_lines = text.splitlines()
            body = "\n".join(all_lines[:200])
            lines.append("")
            lines.append(body)
            if len(all_lines) > 200:
                lines.append(f"... (truncated, showing 200 of {len(all_lines)} lines)")
        else:
            dl = contents.get("download_url")
            lines.append("(binary or undecodable content)")
            if dl:
                lines.append(f"Download: {dl}")
        return "\n".join(lines)
    return f"{where}: no content."


def format_readme(entry: dict[str, Any], owner: str, repo: str) -> str:
    text = decode_file_content(entry)
    name = entry.get("name") or "README"
    lines = [f"README of {owner}/{repo} ({name}):", ""]
    if text is not None:
        all_lines = text.splitlines()
        lines.append("\n".join(all_lines[:200]))
        if len(all_lines) > 200:
            lines.append(f"... (truncated, showing 200 of {len(all_lines)} lines)")
    else:
        lines.append("(could not decode README content)")
    return "\n".join(lines)


def format_commits(commits: list[dict[str, Any]], owner: str, repo: str) -> str:
    if not commits:
        return f"No commits found in {owner}/{repo}."
    lines = [f"Commits in {owner}/{repo} ({len(commits)}):"]
    for c in commits:
        sha = str(c.get("sha") or "")[:8]
        commit = c.get("commit") or {}
        msg = str(commit.get("message") or "").strip().splitlines()
        subject = msg[0] if msg else ""
        author = (commit.get("author") or {}).get("name") or ""
        when = str((commit.get("author") or {}).get("date") or "")[:10]
        lines.append(f"- {sha} {when} {author}: {subject}")
    return "\n".join(lines)


def format_releases(releases: list[dict[str, Any]], owner: str, repo: str) -> str:
    if not releases:
        return f"No releases found in {owner}/{repo}."
    lines = [f"Releases in {owner}/{repo} ({len(releases)}):"]
    for r in releases:
        tag = r.get("tag_name") or ""
        name = str(r.get("name") or "").strip()
        flags = []
        if r.get("draft"):
            flags.append("draft")
        if r.get("prerelease"):
            flags.append("prerelease")
        when = str(r.get("published_at") or r.get("created_at") or "")[:10]
        suffix = f" [{', '.join(flags)}]" if flags else ""
        title = f": {name}" if name and name != tag else ""
        lines.append(f"- {tag}{title} ({when}){suffix}")
    return "\n".join(lines)


def format_user(user: dict[str, Any]) -> str:
    login = user.get("login") or "?"
    lines = [f"User {login}"]
    full = str(user.get("full_name") or "").strip()
    if full:
        lines.append(full)
    meta = []
    if user.get("followers_count") is not None:
        meta.append(f"followers: {user.get('followers_count')}")
    if user.get("following_count") is not None:
        meta.append(f"following: {user.get('following_count')}")
    if user.get("starred_repos_count") is not None:
        meta.append(f"starred: {user.get('starred_repos_count')}")
    if meta:
        lines.append(", ".join(meta))
    email = str(user.get("email") or "").strip()
    if email:
        lines.append(f"Email: {email}")
    if user.get("html_url"):
        lines.append(f"Link: {user.get('html_url')}")
    return "\n".join(lines)
