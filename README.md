# xian-meta

`xian-meta` is the shared standards repo for the `xian-technology` workspace.
It defines the conventions, change-workflow rules, and cross-repo design
contracts that keep the main Xian repositories consistent without forcing every
repo to re-document the same patterns.

This repo holds *standards* and *cross-repo contracts*. It does not hold
runtime code, repo-local backlogs, or implementation details that belong to a
single owning repo.

## Quick Start

Open `docs/REPO_CONVENTIONS.md` first if you are starting a new repo, refactoring
an existing one, or evaluating whether a doc belongs here or in an
implementation repo.

```bash
# Read the canonical structure rules
$EDITOR docs/REPO_CONVENTIONS.md

# Read the pre-push change discipline
$EDITOR docs/CHANGE_WORKFLOW.md

# Run the lightweight workspace structure checker
python3 ./scripts/check_repo_conventions.py --workspace-root ..
```

Common entrypoints by question:

- *What should a root README or `AGENTS.md` look like?* → `docs/README_TEMPLATE.md`, `docs/FOLDER_README_TEMPLATE.md`
- *What runs before push?* → `docs/CHANGE_WORKFLOW.md`
- *Where should a cross-repo design live?* → here, then implement in the owning repo
- *What is Xian for, strategically?* → `docs/XIAN_MISSION_AND_PRODUCT_STRATEGY.md`

## Principles

- **Standards, not implementations.** Anything that defines how Xian repos
  should be structured, validated, or coordinated belongs here. Anything that
  implements behavior belongs in the owning repo.
- **Shared contracts go here first.** When a design spans multiple repos
  (protocol, architecture, workflow), the contract is written here before any
  implementation is started.
- **Repo-local notes stay local.** Internal redesign plans, repo-specific
  follow-ups, and one-repo backlogs belong in that repo's `docs/BACKLOG.md`.
- **Consistency over novelty.** New documentation patterns are introduced here
  before they spread to other repos.
- **Human-first.** READMEs and folder entrypoints are optimized for an engineer
  evaluating or using the repo professionally, not for changelogs or AI-only
  consumption.

## Key Directories

- `docs/` — shared conventions, change-workflow rules, and cross-repo design
  notes. The files in this folder are the authoritative source for repo
  structure, README shape, validation gates, and stack-wide protocol designs.
- `scripts/` — lightweight workspace-wide checks. The
  `check_repo_conventions.py` script validates that the main repos comply with
  the structural rules in `docs/REPO_CONVENTIONS.md`.

## Validation

```bash
python3 ./scripts/check_repo_conventions.py --workspace-root ..
```

The checker walks the workspace root, resolves the main `xian-*` repos, and
reports any deviations from the required-root-files and folder-README rules
defined in `docs/REPO_CONVENTIONS.md`.

## Related Docs

- [AGENTS.md](AGENTS.md) — repo guidelines for AI agents and contributors
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — what `xian-meta` owns and what it intentionally excludes
- [docs/BACKLOG.md](docs/BACKLOG.md) — open work on the standards repo itself
- [docs/REPO_CONVENTIONS.md](docs/REPO_CONVENTIONS.md) — canonical repo structure standard
- [docs/CHANGE_WORKFLOW.md](docs/CHANGE_WORKFLOW.md) — pre-push docs-impact and validation gates
- [docs/README_TEMPLATE.md](docs/README_TEMPLATE.md) — root README shape used by the main repos
- [docs/FOLDER_README_TEMPLATE.md](docs/FOLDER_README_TEMPLATE.md) — short per-folder entrypoint template
- [docs/XIAN_MISSION_AND_PRODUCT_STRATEGY.md](docs/XIAN_MISSION_AND_PRODUCT_STRATEGY.md) — shared mission, principles, and product direction
- [docs/README.md](docs/README.md) — index of every cross-repo design note maintained here
