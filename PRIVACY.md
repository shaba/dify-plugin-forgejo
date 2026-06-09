# Privacy Policy

This plugin (`dify-plugin-forgejo`) does not collect, store or transmit any personal
data to the plugin author or any third party.

- The configured credentials are `base_url` (the URL of the Forgejo or Gitea server you
  choose) and an optional `api_token`. They are stored by your Dify instance, not by the
  plugin author.
- When you invoke a tool, the plugin sends HTTP requests **only** to that `base_url`
  (its `/api/v1` REST API), carrying the parameters you provided (owner, repository, issue
  or pull request numbers, search queries, and any content you submit for write actions),
  and the `api_token` if you configured one. Requests use the User-Agent
  `dify-plugin-forgejo/0.0.1`.
- No analytics, telemetry or external hosts are involved. The plugin itself persists
  nothing.

Your queries and the repository data you read or write are subject to the privacy policy
of the Forgejo or Gitea server configured in `base_url`.
