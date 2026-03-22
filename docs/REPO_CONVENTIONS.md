# Repository Conventions

## Goal

The main `xian-technology` repos should be easy to traverse quickly for both humans and AI agents.

The convention is designed around:

- predictable root files
- a stable place for future work and architecture notes
- short folder-level entrypoints at architectural boundaries

## Required Root Files

Every main repo should have:

- `README.md`
- `AGENTS.md`

Every main repo should also expose two stable internal note entrypoints:

- `docs/ARCHITECTURE.md`
- `docs/BACKLOG.md`

Exception:

- the public docs site repo may keep these internal notes under a hidden `.meta/` directory so they do not become part of the published site.

## Meaning Of The Standard Files

- `README.md`: public repo entrypoint
- `AGENTS.md`: fast AI/operator orientation for the repo
- `docs/ARCHITECTURE.md`: major components, ownership, dependency direction
- `docs/BACKLOG.md`: future work, open problems, follow-up items, and links to deeper notes

## Change Workflow

Every change in a main Xian repo should follow two explicit gates before push:

1. `docs-impact` gate
2. `validation` gate

### Docs-Impact Gate

Before pushing a change, check whether it changes any of these:

- public API shape
- SDK behavior
- CLI behavior or workflow
- node/runtime behavior
- deployment or operator workflow
- monitoring, BDS, snapshots, pruning, or performance surfaces
- contract-author-facing behavior

If yes:

- inspect the relevant section of `xian-docs-web`
- update the docs in the same change set
- treat docs updates as part of the feature/fix, not an optional follow-up

If no docs updates are needed, that should be a deliberate decision, not an omission.

### Validation Gate

Before pushing a change:

- run the preferred local validation commands listed in the repo `AGENTS.md`
- do not push code with known failing validation
- if the change touches multiple repos, validate each changed repo
- if `xian-docs-web` is changed, run its build before push

Each repo should expose a clear preferred validation path in `AGENTS.md`.
If a repo lacks one, add it before expanding the repo further.

## Cross-Repo Rule

When a code change in one repo affects public behavior elsewhere, the change is not complete until the impacted repos are updated as needed.

Typical examples:

- behavior change in `xian-abci` may require updates in `xian-py`, `xian-cli`, `xian-stack`, and `xian-docs-web`
- behavior change in `xian-contracting` may require updates in `xian-abci`, `xian-py`, and `xian-docs-web`
- deployment/runtime changes may require updates in `xian-deploy` and `xian-docs-web`

## Folder-Level READMEs

Add a `README.md` to a folder when that folder is an architectural boundary or a likely starting point.

Typical examples:

- `docs/`
- `src/`
- the main package directory
- `tests/`
- `scripts/`
- `docker/`
- `monitoring/`
- `contracts/`
- `networks/`
- `playbooks/`
- `roles/`
- `workloads/`

Do not add `README.md` to every small utility folder.

## Folder README Content

Each folder README should stay short and answer four questions:

1. What does this folder own?
2. What are the important files or subfolders?
3. What should not be changed casually?
4. Where should a reader go next?

## Naming Guidance

Use stable names for recurring note types:

- `ARCHITECTURE.md`
- `BACKLOG.md`
- `README.md`
- `AGENTS.md`

Keep special-purpose notes when they carry real value, but link them from `BACKLOG.md` instead of leaving them as disconnected one-off files.
