# Repository Guidelines

## Scope
- `xian-meta` is the shared conventions repo for the Xian workspace.
- Keep the guidance here small, stable, and cross-repo.
- This repo should define conventions and stack-wide design contracts, not re-document each implementation repo in detail.
- Do not turn this repo into a general backlog for future work.
- Repo-local implementation notes, internal redesign plans, and repo-specific follow-ups belong in the owning repo.
- Put a design in `xian-meta` only if it defines behavior, structure, or workflow that spans multiple main Xian repos.

## Project Layout
- `docs/REPO_CONVENTIONS.md`: authoritative repo structure standard.
- `docs/FOLDER_README_TEMPLATE.md`: short template for directory-level entrypoints.
- `docs/README.md`: overview of the internal documentation in this repo.

## Workflow
- When the convention changes, update this repo first, then roll the change into the implementation repos.
- Favor consistency over novelty. New documentation patterns should be introduced here before they spread.
- Other Xian repos should point here and follow `docs/REPO_CONVENTIONS.md` for root structure, backlog placement, and folder-level README rules.
- For cross-repo designs, define the shared contract here first, then implement repo-specific details in the owning repos.
