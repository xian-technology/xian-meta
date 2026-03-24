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

These were present when the sweep started and had to be handled explicitly:

- `xian-contracting`
  - local `AGENTS.md` update matching the shared workflow convention
  - local rename drift from `STAMPS_PER_TAU` to `STAMPS_PER_T` in:
    - `src/contracting/constants.py`
    - `tests/integration/test_stamp_deduction.py`
    - `tests/unit/test_revert_on_exception.py`
- `xian-cli`
  - local `uv.lock` drift adding `prometheus-client`, which needed to be
    verified against the real `xian-abci` dependency graph before keeping it

Both caveats were resolved during Phase 2 and should not be reintroduced.

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
  - local caveats resolved:
    - `xian-contracting` drift reviewed and pushed intentionally
    - `xian-cli` lock drift confirmed valid because `xian-abci` now depends on
      `prometheus-client`
  - live `single-node-dev` workflow executed from an isolated validation
    workspace using a dedicated `xian-stack` worktree
  - workflow bugs found and fixed:
    - `xian-cli` JSON writes could not serialize generated genesis payloads
      containing `Datetime`, decimals, or bytes
    - `xian-cli` backend command wrapper hid real `xian-stack` stderr behind a
      generic `CalledProcessError`
    - `xian-stack` runtime readiness probe invoked Docker Compose without first
      loading the stack environment, which broke container startup checks
    - `xian-cli node init` rendered `metrics_host = "127.0.0.1"` into the
      node config, which made the published Docker metrics port unreachable
      from the host even though the exporter itself was healthy
  - regression coverage added in `xian-cli` for:
    - JSON normalization when local genesis contains `Datetime`
    - backend stderr surfacing
    - stack-compatible metrics binding during node initialization
  - live validation result after fixes:
    - `xian network create --init-node` succeeds for a generated
      `single-node-dev` network
    - `xian node start`, `status`, `endpoints`, `health`, `doctor`, and `stop`
      succeed against the isolated node
    - host metrics endpoint `http://127.0.0.1:9108/metrics` is now reachable
    - dashboard status endpoint on the configured host port is reachable
  - next live scenarios:
    - `single-node-indexed` with BDS enabled
    - `consortium-3`
    - snapshot and recovery flows
    - at least one solution-pack walkthrough against a live node
  - live `single-node-indexed` workflow then exposed two service-node bugs in
    `xian-abci`:
    - BDS wrote Python `dict` and `list` values directly into asyncpg JSONB
      parameters during genesis and normal indexed persistence, which caused
      startup failure with `expected str, got dict`
    - BDS storage initialization happened during `Xian.create()` on a different
      event loop than the ABCI runtime loop, which caused asyncpg pool usage to
      fail at runtime with `Future attached to a different loop`
  - fixes implemented and validated locally:
    - JSONB persistence now serializes all direct asyncpg JSONB parameters
      through canonical JSON text before execution
    - BDS storage initialization is deferred into `start_runtime()` so pool
      creation and usage stay on the same runtime loop
  - regression coverage added in `xian-abci` for:
    - genesis and transaction JSONB serialization in BDS persistence
    - runtime-loop-safe BDS startup initialization
  - validation after the indexed-path fixes:
    - targeted BDS/runtime/query tests passed
    - full `xian-abci` validation passed with `260 passed`
  - rerunning the clean indexed service-node stack exposed one last operator bug:
    - BDS status and spool health were live and persisted blocks correctly, but
      `/bds_status` failed over `abci_query` because the query JSON path did not
      normalize builtin Python `datetime` values before encoding the response
  - final indexed-path fix:
    - ABCI JSON normalization now handles builtin `datetime` values and query
      dict/list responses use the canonical ABCI JSON encoder
  - regression coverage extended in `xian-abci`:
    - `test_bds_status_and_spool_queries_use_bds` now exercises a status object
      containing a timezone-aware `datetime`
  - follow-up indexed-path and SDK workflow fixes:
    - `xian-cli` stack-backed node lifecycle commands now pass the selected
      `XIAN_COMETBFT_HOME`, so `start`, `stop`, `status`, `endpoints`, and
      `health` operate on the chosen node profile instead of the stack default
      home
    - `xian-py` now exposes an optional `app` extra for the documented FastAPI
      and uvicorn examples
    - `xian-configs` solution-pack contracts now have an explicit lint gate via
      `scripts/validate-solution-pack-contracts.py`, and the Credits Ledger
      pack contract was fixed to satisfy the current linter rules
    - `xian-py` solution-pack write examples now fail loudly on rejected or
      failed submissions instead of printing false-success hashes
    - `xian-py` simulation and stamp-estimation now canonicalize payloads with
      runtime encoding, which fixed Decimal-valued argument simulation
    - `xian-contracting` stamp deduction now coerces decimal-ish balance values
      from storage before metering and deduction
  - live indexed-network validation completed on the corrected stack-backed
    single-node network `xian-validate-indexed-fixed-1`
  - live Credits Ledger validation found and fixed additional real bugs:
    - BDS transaction persistence assumed `rewards` was always a dict; failed
      transactions could emit `null`, which stalled indexing until restart
    - `IndexedEvent` in `xian-py` preserved `data` and `data_indexed` as raw
      JSON strings instead of decoding them once at the SDK boundary
    - the Credits Ledger projector assumed actor and account fields always
      lived in `event.data`, but indexed events split them into `data_indexed`
    - the Credits Ledger projector did not accept runtime fixed-point payloads
      like `{\"__fixed__\": \"50.5\"}` in event amounts
    - indexed models in `xian-py` only looked at `created`, while BDS returns
      `created_at`
    - stack endpoint output advertised wildcard dashboard hosts like
      `0.0.0.0`; user-facing endpoint discovery now normalizes those to
      loopback URLs
  - live indexed-network validation result after those fixes:
    - `xian node start`, `status`, `endpoints`, `health`, and `stop` work
      against the intended selected node home
    - BDS indexed and caught up cleanly through the live Credits Ledger
      workflow
    - the Credits Ledger admin job, projector worker, and FastAPI service all
      ran successfully against the live indexed node
    - live API writes for issue, burn, and transfer produced matching on-chain
      balances, indexed events, and projected balances/activity
  - next step:
    - run the full relevant validation set for all touched repos, push the
      fixes, and then summarize any remaining follow-up risk after the
      whole-stack sweep
      live health surface reflects the final query fix
  - final live indexed result:
    - `single-node-indexed` now succeeds from a clean isolated workspace
    - `xian node start`, `status`, `endpoints`, `health`, and `doctor`
      succeed against the rebuilt service-node profile
    - BDS persists live blocks and both `/bds_status` and `/bds_spool` answer
      correctly over `abci_query`
    - GraphQL, Prometheus, Grafana, dashboard status, and host metrics are all
      reachable in the live run
  - next live scenarios:
    - `consortium-3`
    - snapshot and recovery flows
    - at least one solution-pack walkthrough against a live node
  - live `Registry / Approval` reference-app validation then completed against
    the indexed single-node network
  - registry validation exposed and resolved additional cross-stack issues:
    - the SDK/example hydration path was still using raw simulation envelopes;
      `xian-py` now exposes `call(...)` for decoded readonly contract returns
      and raises on failed simulated execution
    - the registry projector only read `event.data`, but live BDS payloads can
      split decisive fields into `data_indexed`; the registry projector now
      merges both halves before applying or hydrating state
    - the workflow backend examples had the same authoritative-read issue and
      now use the shared `call(...)` path for `get_item`
    - boolean ABCI query values were mislabeled as `int` because `bool` is a
      subclass of `int`; the node now emits `info = "bool"` and the SDK also
      decodes older mislabeled responses compatibly
    - the registry bootstrap job added approvers but did not fund them with
      enough native balance to pay for approval transactions in the reference
      flow; it now tops up configured signers by default, with `0` disabling
      the top-up
  - live registry validation result after fixes:
    - the initial proposal hydrated correctly from authoritative contract reads
    - the second signer approval succeeded through the FastAPI service
    - the projector applied `ProposalApproved`, `RecordUpserted`, and
      `ProposalExecuted`
    - projected proposal, record, approval, and activity views all matched the
      authoritative on-chain registry state
  - next live scenario:
    - `Workflow Backend` reference-app validation at the same depth
