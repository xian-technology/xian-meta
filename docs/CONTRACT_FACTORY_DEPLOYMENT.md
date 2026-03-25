# Contract Factory Deployment

Status: implemented

This document defines the design for re-enabling contracts deploying contracts
in Xian.

The goal is to restore contract factories in a way that is explicit,
deterministic, indexable, and safe enough for production use.

Implementation landed on `2026-03-25` across `xian-contracting`,
`xian-abci`, and `xian-docs-web`.

## Decision

Xian should allow contracts to deploy contracts again.

This should be done through the public `submission.submit_contract(...)`
entrypoint, not by exposing raw deployment primitives to normal authored
contracts.

The design keeps:

- `submission` as the public deployment boundary
- `ctx.signer` pinned to the original external sender
- `ctx.caller` set to the immediate deploying contract
- constructor/module-body execution under an explicit deployment context
- atomic rollback on failure
- state-driven indexing of deployments in BDS

The design also tightens deployment security relative to the historical model:

- explicit deployment provenance
- explicit constructor context semantics
- explicit raw-source size limits
- explicit deployment-analysis metering

## Why This Feature Should Exist

Contract factories are useful for:

- per-user contracts
- per-market / per-pair contracts
- registries that deploy isolated instances
- DAO- or app-owned modules
- templated product backends built from on-chain components

This fits Xian's direction as a programmable decentralized backend. It is a
real capability improvement, not just feature parity.

## Current State

Today the public deployment path is blocked in the submission contract:

- [submission.s.py](/Users/endogen/Projekte/xian/xian-contracting/src/contracting/contracts/submission.s.py)

The blocking line is:

- `assert ctx.caller == ctx.signer, 'Contract cannot be called from another contract!'`

That means nested calls into `submission.submit_contract(...)` are forbidden.

## Important Current Constraints

### Public deployment is mediated by `submission`

Normal authored contracts do not have a clean public deployment primitive other
than the submission contract.

`__Contract` exists in the runtime stdlib:

- [orm.py](/Users/endogen/Projekte/xian/xian-contracting/src/contracting/stdlib/bridge/orm.py)

But authored contracts are still blocked from naming `__Contract` directly by
the linter, so this is not the normal public interface.

That is good. The public policy boundary should remain `submission`.

### If we simply remove the guard today, constructor semantics are wrong

The current internal submission path is:

- `submission.submit_contract(...)`
- `__Contract().submit(...)`
- [contract.py](/Users/endogen/Projekte/xian/xian-contracting/src/contracting/storage/contract.py)

`Contract.submit(...)` currently executes the new contract module body and
constructor inside the caller's current runtime context, without pushing a new
contract context for the child contract.

This was confirmed locally on `2026-03-25` by executing `Contract.submit(...)`
under a simulated factory deployment context. The child constructor observed:

- `ctx.this == 'submission'`
- `ctx.caller == 'con_factory'`
- `ctx.signer == 'alice'`
- `ctx.entry == ('con_factory', 'deploy')`
- `ctx.submission_name is None`

That is not acceptable for a proper contract-factory model.

### BDS currently only notices direct top-level submissions

Current live contract upsert logic in BDS is gated on the outer transaction
payload being:

- `contract == 'submission'`
- `function == 'submit_contract'`

See:

- [bds.py](/Users/endogen/Projekte/xian/xian-abci/src/xian/services/bds/bds.py)

That means a factory deployment inside some other transaction would not be
indexed correctly unless BDS is changed.

## Goals

- allow contract factories through the normal public submission surface
- define exact constructor and module-body context semantics
- preserve deterministic rollback behavior
- preserve a clean audit trail for who deployed what
- let BDS/indexers discover deployments from any successful transaction
- ensure deployment loops and comment spam are bounded economically

## Non-goals

- no direct public deployment primitive other than `submission`
- no attempt to make deployment free or especially cheap
- no legacy compatibility mode for old nested-deployment behavior
- no requirement that comments be preserved on chain
- no additional governance toggle in v1 of this redesign

## High-Level Model

There are four distinct identities involved in deployment:

- `initiator`: the original external signer of the transaction
- `deployer`: the immediate caller that requested the child deployment
- `owner`: the final owner stored on the child contract
- `developer`: the mutable developer/reward-recipient field

For direct user submission:

- `initiator == deployer == signer address`

For contract-factory submission:

- `initiator == original external signer`
- `deployer == immediate calling contract`

## Canonical Rules

### Public API

Factories deploy child contracts by calling:

- `submission.submit_contract(name=..., code=..., owner=..., constructor_args=...)`

The submission contract remains the public entrypoint.

Host-side helpers such as `Contract.submit(...)` and
`Driver.set_contract_from_source(...)` remain internal tooling surfaces for
tests, genesis building, and operators. They are not the public on-chain policy
boundary.

### Deployment context

When the child contract module body and constructor execute, they must run
under a dedicated deployment context with these values:

- `ctx.this = <new contract name>`
- `ctx.caller = <deployer>`
- `ctx.signer = <initiator>`
- `ctx.owner = <owner argument, or None>`
- `ctx.entry = <original transaction entry point>`
- `ctx.submission_name = <new contract name>`

This deployment context applies to:

- top-level module execution of the child contract
- the child constructor (`@construct`)

After deployment completes or fails, the previous context must be restored
exactly.

### `ctx.entry`

`ctx.entry` must remain the original transaction entry point, not the child
constructor.

This matches existing Xian semantics:

- `ctx.entry` describes the transaction entry function
- it does not change just because execution crosses into another contract

### `ctx.submission_name`

During child deployment, `ctx.submission_name` must equal the child contract
name.

This is true for:

- direct user submissions
- contract-factory submissions
- child module body
- child constructor

### Naming rules

Submission naming rules remain in force:

- non-`sys` callers must use names starting with `con_`
- names must be lowercase
- names must be within the configured length limit

The caller being a contract does not weaken these rules.

### Ownership

`owner` keeps its current meaning:

- it is an explicit deployment argument
- it may be `None`
- it becomes the stored `__owner__`
- it controls owner-gated exported calls as today

There is no new implicit owner default in this redesign.

### Developer attribution

`developer` remains the mutable field used for current developer attribution and
developer-reward routing.

Initial value:

- `developer = deployer`

That means:

- direct user deployment: developer is the user
- factory deployment: developer is the factory contract

This is intentional. The contract that actually deploys the child should own
initial developer control unless it later delegates it.

### Immutable deployment provenance

The redesign adds immutable provenance keys to the child contract:

- `__deployer__ = <deployer>`
- `__initiator__ = <initiator>`

These are separate from `__developer__`.

Reason:

- `__developer__` can change later
- provenance should not

This gives us:

- current developer
- original deployer
- original transaction initiator

all separately.

## Metering and Resource Control

Allowing nested deployments is safe only if the expensive parts of deployment
are explicitly bounded.

### Problem

Today, contract deployment already writes a lot of state and runs code, but the
host-side analysis work:

- parse
- lint
- transform
- compile

is not a clean explicit metering surface of its own.

This matters more once contract code can loop and deploy multiple children in
one transaction.

### Required protections

#### 1. Hard raw-source size limit

Add a hard limit on raw submitted source size:

- `MAX_CONTRACT_SOURCE_BYTES`

This limit is checked against the original submitted source bytes, before
normalization.

Why raw source:

- parser and linter still process comments
- comments should not consume storage bytes
- but excessive comments should still be bounded and charged as processing work

#### 2. Explicit deployment-analysis charge

Add a deployment-specific surcharge inside `Contract.submit(...)`:

- fixed base cost: `DEPLOYMENT_BASE_COST`
- raw-source byte cost: `DEPLOYMENT_COST_PER_RAW_BYTE`

This charge is assessed once per child deployment before parse/lint/compile.

The write metering already charges storage growth for:

- `__source__`
- `__code__`
- metadata keys

So the new deployment surcharge is specifically for host-side analysis cost,
not storage duplication.

#### 3. Existing limits remain in force

The redesign continues to rely on:

- recursion limit in [runtime.py](/Users/endogen/Projekte/xian/xian-contracting/src/contracting/execution/runtime.py)
- write cap in the runtime
- total transaction stamp budget

### No extra count cap in v1

v1 does not introduce a separate `max_contract_deployments_per_tx` cap.

Reason:

- stamps
- write cap
- recursion limit
- raw-source size limit
- deployment surcharge

are sufficient if implemented correctly.

If benchmarking later shows pathological compile-heavy workloads still escape
pricing, a count cap can be added later.

## Comment Handling

Comments should not be preserved on chain as canonical source.

Canonical state should continue to store:

- `__source__`: normalized, comment-free, human-facing source
- `__code__`: canonical runtime source

This matches the current source-storage direction.

However, raw submitted source bytes still matter for deployment metering and
size checks.

That gives the right tradeoff:

- comments do not bloat canonical state
- comments still cost if someone tries to abuse them for parser/compile load

## Execution Semantics

### Deployment module-body execution

The child contract module body executes under the deployment context.

This is important because top-level code can:

- read `ctx`
- initialize state indirectly
- import or call other contracts

### Constructor execution

The child constructor executes under the same deployment context.

That means the constructor sees:

- `ctx.this = child contract`
- `ctx.caller = deployer`
- `ctx.signer = initiator`

### Nested deployments from constructors

Constructors may deploy more contracts.

Those nested child deployments follow the same rules recursively:

- immediate deployer becomes the current child contract
- initiator remains the original external signer
- recursion limit applies

### Rollback

Deployment is atomic inside the outer transaction.

If any part fails:

- child compilation
- child module-body execution
- child constructor
- nested child deployment

then the entire outer transaction reverts exactly as today.

No partially deployed child contract may remain.

## Submission Contract Design

The public submission contract should be updated as follows.

### Remove the historical ban

Remove:

- `assert ctx.caller == ctx.signer`

### Keep submission as the public boundary

The submission contract still enforces:

- name formatting
- naming prefix rules
- any future deployment policy controls

### Emit a deployment event

Add a `ContractDeployed` event to the submission contract.

Recommended payload:

- indexed: `name`
- data: `owner`, `developer`

The BDS event row already stores:

- `caller` -> deployer
- `signer` -> initiator

So the event does not need to duplicate those values.

This event is not the canonical source of truth for deployment state, but it is
useful for:

- explorers
- event consumers
- audit trails

## BDS and Indexing

BDS must stop detecting deployments only from the outer transaction payload.

### New detection rule

For every successful transaction:

- inspect state changes
- group keys by contract prefix
- detect any contract prefix that wrote either:
  - `<name>.__source__`
  - `<name>.__code__`

That indicates a contract deployment or contract-state patch that replaced a
contract definition.

### Upsert behavior

For each detected contract deployment:

- prefer `__source__` as display source
- fall back to `__code__` if `__source__` is absent
- associate the child contract with the outer transaction hash and block

This must support:

- direct submissions
- factory submissions
- multiple child deployments in one transaction

### Event handling

BDS should also persist the new `ContractDeployed` event, but indexing must not
depend on the event.

State changes remain the authoritative detector.

## Metadata and State Keys

Canonical contract metadata after deployment should include:

- `name.__source__`
- `name.__code__`
- `name.__owner__`
- `name.__developer__`
- `name.__deployer__`
- `name.__initiator__`
- `name.__submitted__`

This is the complete minimal metadata set for the redesigned model.

## Security Review

### 1. Factory spam

Risk:

- one contract deploys many child contracts in a single transaction

Mitigation:

- transaction stamps
- runtime write cap
- recursion limit
- raw-source size limit
- deployment-analysis surcharge

### 2. Comment spam / parser abuse

Risk:

- giant comment blocks add parser and compiler cost

Mitigation:

- raw-source byte limit
- deployment surcharge based on raw submitted bytes
- canonical stored source strips comments

### 3. Hidden provenance

Risk:

- a child contract appears to come from a user while actually being controlled
  by a factory

Mitigation:

- immutable `__deployer__`
- immutable `__initiator__`
- `ContractDeployed` event
- BDS event rows already carry caller/signer

### 4. Constructor privilege confusion

Risk:

- child constructor sees `ctx.this = submission` or otherwise wrong identity

Mitigation:

- explicit deployment context state for module body and constructor

### 5. Partial child deployment

Risk:

- some metadata/state survives a failed nested deployment

Mitigation:

- deployment continues to run inside the outer transactional driver state
- no special commit path
- normal rollback semantics apply

### 6. Direct low-level deployment bypass

Risk:

- authored contracts try to call `__Contract().submit(...)` directly

Mitigation:

- keep linter ban on leading-underscore names for authored contracts
- keep `submission` as the public API boundary

## Cross-Repo Changes Required

### `xian-contracting`

- remove the `ctx.caller == ctx.signer` ban from submission
- add deployment event
- add immutable provenance keys
- add explicit deployment context push/pop
- add source-size limit
- add deployment-analysis metering

### `xian-abci`

- update BDS contract indexing to detect deployments from state changes
- persist the new deployment event normally
- ensure query and dashboard paths show new contract provenance cleanly if
  desired

### `xian-py`

- no mandatory API change for basic deployment
- optional future helper APIs can expose deployment provenance

### `xian-docs-web`

- update submission/factory docs
- update context docs for constructor deployment semantics
- document provenance metadata and deployment event

## Test Plan

The implementation is not complete until all of these exist.

### Contract runtime tests

- direct user deploy still works
- contract factory deploy works
- child constructor sees:
  - `ctx.this = child`
  - `ctx.caller = factory`
  - `ctx.signer = user`
  - `ctx.entry = outer tx entry`
  - `ctx.submission_name = child`
- module body sees the same values
- nested constructor deploy works
- recursion limit still triggers correctly

### Rollback tests

- child constructor failure leaves no child state
- nested child failure rolls back outer transaction
- duplicate child name rolls back outer transaction

### Metering and limits

- oversize raw source is rejected
- comment-heavy source is charged by raw-source size
- repeated child deployments consume measurable extra stamps

### ABCI / BDS tests

- direct submission still indexes contract creation
- factory submission indexes child contract creation
- multiple child deployments in one tx are all indexed
- `ContractDeployed` events are persisted with correct caller/signer

## Recommended Implementation Order

1. Add explicit deployment context support in `xian-contracting`
2. Add raw-source size limit and deployment-analysis metering
3. Remove the submission guard and add the deployment event
4. Add immutable provenance keys
5. Update BDS to detect deployments from state changes
6. Add runtime, ABCI, and BDS tests
7. Update docs

## Recommendation

Xian should restore contract factories.

But the correct version is not just "remove one assert".

The proper version is:

- explicit nested deployment semantics
- explicit provenance
- explicit pricing for deployment analysis
- explicit BDS detection for child deployments

That gives Xian the feature back in a form that is cleaner and more secure than
the historical one.
