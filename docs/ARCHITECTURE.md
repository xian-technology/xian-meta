# Architecture

`xian-meta` is the shared standards repo for the main `xian-technology`
workspace.

It owns:

- repository and documentation conventions that should be consistent across the
  main repos
- shared pre-push workflow rules such as docs-impact and validation gates
- cross-repo protocol or architectural designs that define a common contract
  before implementation

It does not own:

- repo-local implementation notes
- repo-local future work or redesign plans
- day-to-day code or runtime behavior in the implementation repos

Main contents:

- `docs/REPO_CONVENTIONS.md`: canonical structure and naming guidance
- `docs/CHANGE_WORKFLOW.md`: common change discipline before push
- `docs/README_TEMPLATE.md`: root README template used to normalize repos
- `docs/`: stack-wide protocol and design documents when a change spans
  multiple repos
- `scripts/check_repo_conventions.py`: lightweight checker for the shared repo
  structure rules

Use `xian-meta` when a change defines a shared contract across multiple repos.
If a note is mostly about one repo's internals, keep it in that repo instead.
