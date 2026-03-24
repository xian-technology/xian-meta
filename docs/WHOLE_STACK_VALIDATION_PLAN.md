# Whole-Stack Validation And Hardening Plan

Date started: 2026-03-24

## Goal

Run a deliberate quality sweep across the major Xian repos, fix the bugs and
rough edges we find, add missing regression coverage where needed, and validate
the stack end to end with real local nodes and network workflows.

This plan is intentionally resumable. If work stops mid-sweep, the next session
should continue from the current phase and update this file before expanding the
scope again.

## Repos In Scope

- `xian-abci`
- `xian-contracting`
- `xian-py`
- `xian-cli`
- `xian-stack`
- `xian-configs`
- `xian-deploy`
- `xian-docs-web`
- `xian-linter`
- `xian-meta`

## Sweep Principles

- Start with baseline validation before changing behavior.
- Prefer fixes that improve correctness, clarity, operator UX, and developer UX
  over benchmark-only work.
- If behavior changes, update `xian-docs-web` in the same slice.
- If a fix spans repos, record the contract or workflow change here and in the
  owning repo notes.
- Treat consensus-sensitive changes conservatively and add regression tests in
  the same slice.
- Avoid clobbering unrelated local workspace changes; record them explicitly
  and reconcile them deliberately.

## Current Local Workspace Caveats

These were present when the sweep started and must be handled explicitly:

- `xian-contracting`
  - local `AGENTS.md` update matching the shared workflow convention
  - local rename drift from `STAMPS_PER_TAU` to `STAMPS_PER_T` in:
    - `src/contracting/constants.py`
    - `tests/integration/test_stamp_deduction.py`
    - `tests/unit/test_revert_on_exception.py`
- `xian-cli`
  - local `uv.lock` drift adding `prometheus-client`, but the dependency must
    be checked against the declared package metadata before keeping it

These local differences should be either pushed intentionally during the sweep
or discarded after review. Do not leave them ambiguous.

## Validation Matrix

### Repo Validation Commands

- `xian-abci`
  - `./scripts/validate-repo.sh`
- `xian-contracting`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pytest`
- `xian-py`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pytest`
- `xian-cli`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pytest -q`
- `xian-stack`
  - `python3 ./scripts/backend.py validate`
  - `python3 ./scripts/backend.py smoke` or `make smoke` when appropriate
- `xian-configs`
  - `uv run --project ../xian-cli python ./scripts/validate-manifests.py`
- `xian-deploy`
  - `make validate`
- `xian-docs-web`
  - `npm run build`
- `xian-linter`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pytest`
- `xian-meta`
  - `python3 ./scripts/check_repo_conventions.py --workspace-root ..`

### Live Workflow Validation Targets

After repo-level validation is green, run real workflow checks covering:

1. Local single-node developer network
2. Local single-node indexed network
3. Local multi-node consortium-style network
4. BDS-enabled node behavior
5. Snapshot / state-sync / recovery flows
6. Golden-path SDK workflows
7. At least one solution-pack walkthrough end to end

## Phases

### Phase 1: Baseline And Triage

- run the baseline validation matrix across the major repos
- record failures, flaky paths, and obvious weak spots
- classify findings into:
  - correctness bugs
  - missing tests
  - workflow breakage
  - docs drift
  - simplification / UX improvements

### Phase 2: Repo-Level Hardening

- fix failing validations
- add missing regression tests where behavior is weakly covered
- resolve known local drift cleanly
- update docs when behavior or public workflows change

### Phase 3: Cross-Repo Workflow Hardening

- verify the golden path:
  - create or select network template
  - configure node
  - start stack
  - deploy contracts
  - integrate with `xian-py`
  - inspect and monitor the node
- fix friction, ambiguity, or broken assumptions found along the path

### Phase 4: Live Network And Recovery Validation

- run local nodes and networks under realistic workflows
- verify:
  - status / endpoints / health / doctor flows
  - BDS ingestion and indexed reads
  - snapshots and state sync
  - solution-pack examples
- fix bugs or simplify operator flows if the real runs expose them

### Phase 5: Final Sweep And Summary

- rerun the full relevant validation set
- confirm touched repos are clean
- summarize:
  - what was fixed
  - what was extended
  - what remains as follow-up

## Current Execution Order

1. baseline validation for the safest clean repos first:
   - `xian-meta`
   - `xian-docs-web`
   - `xian-configs`
   - `xian-deploy`
   - `xian-linter`
2. inspect and resolve the existing local drift in:
   - `xian-contracting`
   - `xian-cli`
3. run core code validations in:
   - `xian-py`
   - `xian-contracting`
   - `xian-cli`
   - `xian-abci`
   - `xian-stack`
4. start fixing failures and coverage gaps in priority order
5. move to live node and network validation

## Progress Log

- 2026-03-24
  - plan created
  - repo survey completed
  - initial local workspace caveats recorded
  - baseline validation matrix executed:
    - `xian-meta` convention checker
    - `xian-docs-web` build
    - `xian-configs` manifest validation
    - `xian-deploy` validation
    - `xian-linter` lint/format/tests
    - `xian-py` lint/format/tests
    - `xian-cli` lint/format/tests
    - `xian-contracting` lint/format/tests
    - `xian-abci` full repo validation
    - `xian-stack` backend validation
  - failures found and resolved in the baseline phase:
    - root `README.md` structure drift in `xian-abci`, `xian-contracting`,
      and `xian-linter`
    - format-gate drift in `xian-py`, `xian-contracting`, and `xian-linter`
    - invalid local `uv.lock` drift in `xian-cli` discarded
  - baseline result:
    - repo-level validation now green across the major codebases
    - next phase is live node/network and workflow validation
