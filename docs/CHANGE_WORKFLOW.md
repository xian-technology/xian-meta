# Change Workflow

Use this as the practical checklist for changes in the main Xian repos.

## Before Push

### 1. Docs Impact

Ask:

- does this change any public or operator-visible behavior?
- does it change APIs, workflows, semantics, limits, monitoring, or deployment behavior?

If yes:

- inspect the relevant pages in `xian-docs-web`
- update them in the same change set

If no:

- make that a deliberate conclusion, not a skipped step

## 2. Validation

Run the preferred local validation commands from the repo `AGENTS.md`.

Rules:

- do not push with known failing validation
- if multiple repos changed, validate each changed repo
- if docs changed, build `xian-docs-web`

## 3. Cross-Repo Review

Check whether the behavior change leaks across repo boundaries.

Common examples:

- node/runtime changes -> `xian-docs-web`, `xian-py`, `xian-cli`, `xian-stack`
- contract-engine changes -> `xian-abci`, `xian-py`, `xian-docs-web`
- deployment changes -> `xian-deploy`, `xian-docs-web`

## Goal

The point is not bureaucracy. The point is:

- docs stay current
- pushed code is already validated
- cross-repo drift is reduced

