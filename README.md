# xian-meta

`xian-meta` defines the shared repository conventions and stack-wide design
standards for the main `xian-technology` repos.

## Scope

This repo owns:

- root-level repo structure
- AI-facing notes and backlog locations
- folder-level `README.md` guidance
- cross-repo documentation conventions
- cross-repo protocol and workflow design notes when a change spans the whole stack

This repo does not own:

- repo-local implementation details
- repo-local backlog items
- repo-local redesign notes
- day-to-day code ownership in the implementation repos

## Key Directories

- `docs/`: shared conventions, workflow rules, and cross-repo design contracts
- `scripts/`: lightweight tooling for checking repo-wide standards

## Validation

```bash
python3 ./scripts/check_repo_conventions.py --workspace-root ..
```

## Related Docs

- [AGENTS.md](AGENTS.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/BACKLOG.md](docs/BACKLOG.md)
- [docs/REPO_CONVENTIONS.md](docs/REPO_CONVENTIONS.md)
- [docs/CHANGE_WORKFLOW.md](docs/CHANGE_WORKFLOW.md)
