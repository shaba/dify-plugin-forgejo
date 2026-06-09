"""Pure Forgejo/Gitea plugin core: REST client, repo/issue/PR logic, formatting.

No dify_plugin dependency. Forgejo is a Gitea fork; both share the /api/v1 REST API,
so this client works against either.
"""
