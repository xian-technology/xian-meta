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
- `check_rust_toolchain_parity.py`: checks that every Rust toolchain pin in
  the `xian-contracting` workflows equals the Rust version of the xian-stack
  node image, so CI, release wheels and the node build use one compiler
- `report_workspace_shas.py`: reports resolved sibling Git refs and SHAs for
  local debugging and CI job summaries
- `graphify_workspace.py`: checks working-file and graph freshness, and
  refreshes directed local Graphify indexes for non-exempt repos
- `benchmark_code_graphs.py`: compares existing isolated Graphify and GitNexus
  indexes against the source-reviewed caller fixtures in `tests/fixtures/`
- `verify_test_isolation.py`: runs two coordinated pytest processes against the
  actual ABCI and contracting fixtures, checking that one process can flush its
  storage and delete its node home without affecting the other. It also checks
  that the next test receives fresh directories. `isolation_probe.py` supplies
  the temporary tests; it is not a standalone test suite.

Run the isolation check after installing each repository's test environment:

```bash
python3 scripts/verify_test_isolation.py --workspace-root ..
```

It uses each repository's `.venv/bin/python`. Use `--repo xian-abci` or
`--repo xian-contracting` to select a repository, and
`--python xian-abci=/absolute/path/to/python` to override its interpreter.
The check requires a supported POSIX node platform and removes its temporary
probes and child processes, including on failure.

Do not turn this folder into a general automation dump. Keep it limited to
workspace-wide convention helpers.
