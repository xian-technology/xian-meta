# Scripts

This folder contains lightweight tooling that helps keep the shared `xian-meta`
conventions enforceable.

Files:

- `bootstrap_workspace.py`: reads `../workspace-repos.json` and clones missing
  sibling repos into the expected local layout, or prints commands with
  `--dry-run`
- `check_repo_conventions.py`: checks required root files and root README
  section headings across repos declared in `../workspace-repos.json`
- `report_workspace_shas.py`: reports resolved sibling Git refs and SHAs for
  local debugging and CI job summaries

Do not turn this folder into a general automation dump. Keep it limited to
workspace-wide convention helpers.
