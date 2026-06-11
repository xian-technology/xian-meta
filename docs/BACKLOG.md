# Backlog

Open follow-up items for `xian-meta` itself:

- decide whether the convention checker should also validate boundary-folder
  `README.md` coverage, not just root structure
- extend the convention checker's repo list once the remaining app/product
  repos carry `AGENTS.md` plus `docs/ARCHITECTURE.md` and `docs/BACKLOG.md`
- add a small template for `docs/ARCHITECTURE.md` and `docs/BACKLOG.md`
  contents so repo-local notes stay as consistent as the root README files
- review whether the main repos should share a common `CONTRIBUTING.md`
  convention in addition to `AGENTS.md`
- keep completed implementation plans out of `docs/` once the current behavior
  is covered by repo-local or public docs

Done: the shared-foundations cleanup in `docs/SHARED_FOUNDATIONS_PLAN.md`
(accounts extracted to `xian-accounts`, decompiler retired in favor of
canonical stored source), and CI for
`scripts/check_repo_conventions.py` in the Validate workflow.

Cross-repo protocol and architecture designs do not belong in this backlog
unless the follow-up work is specifically about `xian-meta` itself.
