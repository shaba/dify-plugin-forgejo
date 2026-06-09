import pytest

from forgejo_client.errors import NotFound
from forgejo_client.repos import (
    decode_file_content,
    find_readme_entry,
    format_commits,
    format_contents,
    format_readme,
    format_releases,
    format_repo,
    format_repo_list,
    format_user,
    get_contents,
    get_readme,
    get_repo,
    list_commits,
    list_releases,
    list_repos,
    search_repos,
)


def test_get_contents_percent_encodes_path(make_capturing):
    f = make_capturing(200, {"type": "file"})
    get_contents("https://example.com", "octo", "demo", "docs/a b?c#d.md", fetch=f)
    url = f.calls[-1]["url"]
    # The special characters must be encoded, separators preserved, and no
    # bogus query string injected from the '?'.
    assert url.endswith("/repos/octo/demo/contents/docs/a%20b%3Fc%23d.md")


def test_search_repos_sends_query(make_capturing):
    f = make_capturing(200, {"data": []})
    search_repos("https://example.com", "demo", limit=30, fetch=f)
    url = f.calls[-1]["url"]
    assert "/repos/search?" in url
    assert "q=demo" in url
    assert "limit=30" in url


def test_list_commits_sends_sha_and_path(make_capturing):
    f = make_capturing(200, [])
    list_commits("https://example.com", "octo", "demo", sha="main",
                 path="src/a.py", limit=15, fetch=f)
    url = f.calls[-1]["url"]
    assert "/repos/octo/demo/commits?" in url
    assert "sha=main" in url
    assert "path=src" in url  # value is urlencoded
    assert "limit=15" in url


def test_get_repo_and_format(fixtures, make_static):
    repo = get_repo("https://example.com", "octo", "demo",
                    fetch=make_static(fixtures("repo.json")))
    assert repo["full_name"] == "octo/demo"
    text = format_repo(repo)
    assert text.startswith("Repository octo/demo")
    assert "stars: 42" in text
    assert "Default branch: main" in text
    assert "{" not in text


def test_search_repos_unwraps_data(fixtures, make_static):
    repos = search_repos("https://example.com", "demo",
                         fetch=make_static(fixtures("search_repos.json")))
    assert len(repos) == 2
    text = format_repo_list(repos, 'Repositories matching "demo"')
    assert text.startswith('Repositories matching "demo" (2):')
    assert "octo/demo" in text


def test_list_repos_user_path(fixtures, make_static):
    repos = list_repos("https://example.com", "octo",
                       fetch=make_static([fixtures("repo.json")]))
    assert repos[0]["name"] == "demo"


def test_format_repo_list_empty():
    assert "none found" in format_repo_list([], "Repositories")


def test_format_contents_directory(fixtures):
    listing = fixtures("contents_dir.json")
    text = format_contents(listing, "octo", "demo", "")
    assert "Directory octo/demo (3 entries)" in text
    assert "[dir] src" in text
    assert "[file] README.md" in text


def test_format_contents_file_decodes(fixtures):
    entry = fixtures("contents_file.json")
    text = format_contents(entry, "octo", "demo", "README.md")
    assert "File octo/demo/README.md" in text
    assert "Hello world README." in text


def test_get_readme_finds_and_decodes(fixtures):
    routes = [fixtures("contents_dir.json"), fixtures("contents_file.json")]
    calls = {"n": 0}

    def f(method, url, *, token=None, json_body=None, timeout=30):
        idx = calls["n"]
        calls["n"] += 1
        return 200, routes[idx]

    entry = get_readme("https://example.com", "octo", "demo", fetch=f)
    text = format_readme(entry, "octo", "demo")
    assert "README of octo/demo (README.md)" in text
    assert "Hello world README." in text


def test_get_readme_raises_not_found_when_no_readme_in_listing():
    # Root listing is a valid directory but contains no README entry; the
    # NotFound branch must fire end-to-end (no second contents fetch happens).
    listing = [
        {"name": "main.py", "type": "file"},
        {"name": "src", "type": "dir"},
    ]
    calls = {"n": 0}

    def f(method, url, *, token=None, json_body=None, timeout=30):
        calls["n"] += 1
        return 200, listing

    with pytest.raises(NotFound):
        get_readme("https://example.com", "octo", "demo", fetch=f)
    # Only the root listing was fetched; no README file fetch was attempted.
    assert calls["n"] == 1


def test_list_commits_and_format(fixtures, make_static):
    commits = list_commits("https://example.com", "octo", "demo",
                           fetch=make_static(fixtures("commits.json")))
    text = format_commits(commits, "octo", "demo")
    assert "Commits in octo/demo (2)" in text
    assert "abcdef12" in text
    assert "Fix the bug" in text
    # only the subject line, not the longer body
    assert "Longer description" not in text


def test_list_releases_and_format(fixtures, make_static):
    releases = list_releases("https://example.com", "octo", "demo",
                             fetch=make_static(fixtures("releases.json")))
    text = format_releases(releases, "octo", "demo")
    assert "Releases in octo/demo (2)" in text
    assert "v1.0.0: First stable" in text
    assert "[prerelease]" in text


def test_decode_file_content_empty_file_is_empty_string_not_none():
    # An empty file has a present-but-empty content field; it must decode to ""
    # (distinct from absent content, which stays None).
    assert decode_file_content({"encoding": "base64", "content": ""}) == ""
    assert decode_file_content({"encoding": "base64"}) is None
    assert decode_file_content({"encoding": "base64", "content": None}) is None


def test_find_readme_entry_prefers_canonical_then_prefix():
    listing = [
        {"name": "main.py", "type": "file"},
        {"name": "README.md", "type": "file"},
    ]
    assert find_readme_entry(listing)["name"] == "README.md"
    # Falls back to any readme-prefixed name when no canonical match exists.
    assert find_readme_entry([{"name": "Readme.adoc", "type": "file"}])["name"] == "Readme.adoc"
    # No README / not a listing -> None.
    assert find_readme_entry([{"name": "main.py", "type": "file"}]) is None
    assert find_readme_entry({"not": "a list"}) is None


def test_format_user(fixtures):
    user = fixtures("user.json")
    text = format_user(user)
    assert text.startswith("User alice")
    assert "followers: 10" in text
    assert "alice@example.com" in text
