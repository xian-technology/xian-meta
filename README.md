# xian-meta

`xian-meta` is the shared standards repo for the main `xian-technology`
repositories. It keeps repo conventions, change-workflow rules, and cross-repo
design notes in one stable place.

## Quick Start

Use this repo when you need to answer one of these questions:

- What is the shared repo structure?
- What should a root README or `AGENTS.md` contain?
- Which docs and validation steps must happen before push?
- Where should a cross-repo design live before implementation starts?

The main entrypoints are:

- [docs/REPO_CONVENTIONS.md](docs/REPO_CONVENTIONS.md)
- [docs/CHANGE_WORKFLOW.md](docs/CHANGE_WORKFLOW.md)
- [docs/XIAN_MISSION_AND_PRODUCT_STRATEGY.md](docs/XIAN_MISSION_AND_PRODUCT_STRATEGY.md)

## Principles

- `xian-meta` is for shared standards and cross-repo design contracts.
- Repo-local implementation details, redesign notes, and backlogs belong in the
  owning repo.
- The goal is consistency without turning every repo into the same document.
- Human-first repo entrypoints and correct dependency boundaries matter as much
  as AI discoverability.

## Key Directories

- `docs/`: shared conventions, workflow rules, and cross-repo design notes
- `scripts/`: lightweight checks for workspace-wide repo standards

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
- [docs/CORE_REPO_CLEANUP_PLAN.md](docs/CORE_REPO_CLEANUP_PLAN.md)
