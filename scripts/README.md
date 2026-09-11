# Scripts

This folder contains lightweight tooling that helps keep the shared `xian-meta`
conventions enforceable.

Files:

- `bootstrap_workspace.py`: reads `../workspace-repos.json` and clones missing
  sibling repos into the expected local layout, or prints commands with
  `--dry-run`
- `check_repo_conventions.py`: checks required root files and root README
  section headings across repos declared in `../workspace-repos.json`
- `check_release_helper_parity.py`: checks that the SDK and linter release
  helpers remain byte-identical; edit both copies together until they use a
  shared published helper
- `report_workspace_shas.py`: reports resolved sibling Git refs and SHAs for
  local debugging and CI job summaries
- `graphify_workspace.py`: checks working-file and graph freshness, and
  refreshes directed local Graphify indexes for non-exempt repos
- `benchmark_code_graphs.py`: compares existing isolated Graphify and GitNexus
  indexes against the source-reviewed caller fixtures in `tests/fixtures/`

Do not turn this folder into a general automation dump. Keep it limited to
workspace-wide convention helpers.
