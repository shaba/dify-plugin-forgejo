# dify-plugin-forgejo

A Dify tool plugin for [Forgejo](https://forgejo.org/). It reads and writes repositories,
issues, pull requests, commits and releases on any Forgejo server. The target server is
configured per credential via `base_url`, so a single installation works with any
instance.

**Works with Gitea too.** Forgejo is a fork of Gitea and both expose the same `/api/v1`
REST API, so every tool here works against a Gitea server as well.

## Configuration

- `base_url` (required) — base URL of the Forgejo or Gitea server, e.g.
  `https://example.com` (the REST API is served under `/api/v1`).
- `api_token` (optional) — a personal access token. It is optional for public read access,
  but required for private data and for all write tools. Write tools succeed only if the
  token carries the matching scope.

Credentials are validated by calling `/api/v1/user` (when a token is set) or
`/api/v1/version` otherwise.

## Tools

### Read

- `repo_info` — repository metadata (description, language, stars, forks, open issues,
  default branch).
- `list_repos` — repositories of a user or organization, or your own if a token is set and
  no username is given.
- `search_repos` — search repositories on the server by keywords (`/repos/search`).
- `repo_contents` — read a file's decoded content or list a directory at a `path`/`ref`.
- `repo_commits` — recent commits, optionally on a given branch/ref.
- `repo_readme` — fetch and decode the repository's README.
- `repo_releases` — releases with tag, name, draft/prerelease flags and date.
- `list_issues` — issues filtered by state and optional keywords.
- `get_issue` — a single issue with its comments.
- `list_pulls` — pull requests filtered by state.
- `get_pull` — a single pull request.
- `user_info` — a user's profile, or your own if a token is set and no username is given.

### Write

These require an `api_token` with write scope on the target repository. There is no extra
toggle: a tool simply fails if the token lacks the scope.

- `create_issue` — open a new issue.
- `issue_comment` — comment on an issue or a pull request (shared endpoint).
- `create_pull` — open a pull request from a head branch into a base branch.
- `merge_pull` — merge a pull request (merge, squash, rebase, rebase-merge).

## Development

```sh
python3 -m pytest -q
ruff check .
yamllint .
```

The Forgejo/Gitea logic (REST client, repo/issue/PR fetch, write actions, formatting)
lives in the `forgejo_client` package, which is independent of the Dify SDK and covered by
unit tests with a mocked `fetch` callable. The tool and provider classes are thin adapters
over it.

Forgejo/Gitea REST API reference: <https://code.forgejo.org/api/swagger> (Gitea swagger:
<https://gitea.com/api/swagger>).

## Credits

The plugin icon is the [Forgejo logo](https://codeberg.org/forgejo/governance/src/branch/main/branding) by Caesar Schinas, licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (used unmodified, see `_assets/icon.LICENSE`).

## License

Apache-2.0. Copyright © 2026 Alexey Shabalin.

## Repository

<https://github.com/shaba/dify-plugin-forgejo> — issues and pull requests welcome.
