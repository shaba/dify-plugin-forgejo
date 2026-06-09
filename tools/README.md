# tools

Each tool is a pair: `<tool>.yaml` (identity + description.llm + parameters) and
`<tool>.py` (`class <Tool>(Tool)` with `_invoke(...) -> Generator[ToolInvokeMessage]`).
Register every tool in `provider/forgejo.yaml` under `tools:`.

The tools are thin adapters: they read `base_url` + `api_token` from credentials,
validate parameters, call the pure `forgejo_client` package and format the result into
compact English text plus a small JSON message. The shared credential helper lives in
`tools/_common.py`.
