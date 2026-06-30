# Repository Guidelines

## Scope
- `xian-meta` is the shared conventions repo for the Xian workspace.
- Keep the guidance here small, stable, and cross-repo.
- This repo should define conventions and stack-wide design contracts, not re-document each implementation repo in detail.
- Do not turn this repo into a general backlog for future work.
- Repo-local implementation notes, internal redesign plans, and repo-specific follow-ups belong in the owning repo.
- Put a design in `xian-meta` only if it defines behavior, structure, or workflow that spans multiple main Xian repos.

## Project Layout
- `workspace-repos.json`: canonical sibling repo manifest, convention tiers, default clone policy, and explicit exemptions.
- `docs/WORKSPACE.md`: progressive-disclosure front door for the full sibling workspace.
- `docs/REPO_CONVENTIONS.md`: authoritative repo structure standard.
- `docs/FOLDER_README_TEMPLATE.md`: short template for directory-level entrypoints.
- `docs/README.md`: overview of the internal documentation in this repo.
- `docs/MAINNET_LAUNCH_PLAN.md`: future public-network launch checklist for the current codebase.
- `docs/COMPILER_RUNTIME_LAUNCH_STATUS.md`: cross-repo compiler/runtime readiness page.

## Progressive Disclosure
- Start with `docs/WORKSPACE.md` for workspace orientation, then move to the owning repo's `AGENTS.md` and `README.md`.
- Use `workspace-repos.json` to decide which sibling repos are in scope and which repos are explicitly exempt.
- Use `docs/REPO_CONVENTIONS.md` for root-file and tier rules before changing repo structure.
- Use `docs/CHANGE_WORKFLOW.md` before pushing multi-repo work.
- Use `docs/MAINNET_LAUNCH_PLAN.md` and `docs/COMPILER_RUNTIME_LAUNCH_STATUS.md` for launch-readiness questions instead of spreading launch status across repo-local notes.
- Keep current-code defaults local unless a future launch manifest has been accepted.

## Workflow
- When the convention changes, update this repo first, then roll the change into the implementation repos.
- Favor consistency over novelty. New documentation patterns should be introduced here before they spread.
- Other Xian repos should point here and follow `docs/REPO_CONVENTIONS.md` for root structure, backlog placement, and folder-level README rules.
- For cross-repo designs, define the shared contract here first, then implement repo-specific details in the owning repos.

## Shared Agent Practices
- Keep changes clean, modular, and professional. Prefer small, cohesive modules, clear naming, explicit boundaries, and tests over quick patches.
- When code behavior, public APIs, user workflows, operator workflows, or configuration semantics change, check whether `../xian-docs-web` needs corresponding documentation updates. If this repo is `xian-docs-web`, update the relevant published docs in place. Write durable user/developer documentation, not a changelog entry.
- For codebase questions, use the local graph first when `graphify-out/graph.json` exists: run `graphify query "<question>"`; use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts.
- Dirty `graphify-out/` files are expected after hooks or incremental updates and are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- Use `graphify-out/wiki/index.md` for broad navigation when it exists. Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not surface enough context.
- For any non-trivial code change, update the local graph before final verification when `graphify-out/graph.json` exists. Run `graphify update .` from the repo root, or `graphify update . --force` when deletions or refactors intentionally shrink the graph.
- After updating the graph, check cross-repo impact before finishing: query the local graph, inspect paths with `graphify path` or `graphify explain`, and note any affected sibling repos.
- If graphify or dependency analysis shows affected sibling repos, update those repos in the same change when the impact is real and the fix is in scope.
- Treat `graphify-out/` as a generated local artifact. Do not commit it.
