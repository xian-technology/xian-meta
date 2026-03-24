# Golden Path Roadmap

## Status

Active cross-repo implementation roadmap.

This document turns the product strategy into an ordered execution plan for
the main Xian repos. It is intended to be resumable: if work stops midstream,
the next useful steps should still be obvious from this file.

## Purpose

The goal of this roadmap is to make Xian feel like the easiest programmable
decentralized backend to use from a normal software stack.

That means the next work should prioritize:

- the application integration path
- network creation and deployment simplicity
- monitoring, recovery, and operations clarity
- a small set of opinionated templates
- incremental docs updates as features land

It should not prioritize:

- throughput-first work
- VM implementation as the immediate next milestone
- protocol expansion without a clear product payoff

## Golden Path Definition

The golden path should let a normal engineering team do this with minimal
guesswork:

1. create a purposeful network from a template
2. start it locally or remotely
3. deploy one or more contracts
4. integrate it from a Python service
5. query state, history, and events cleanly
6. monitor the node and recover it when something goes wrong

The stack should eventually support a polished version of that flow in under
thirty minutes for a new user.

## Cross-Repo Principles For This Roadmap

- Every implemented feature that changes user-facing behavior must be reviewed
  for docs impact in `xian-docs-web`.
- Docs should be updated incrementally with implementation, not as a large
  cleanup pass afterward.
- Each completed slice should update the relevant backlog/roadmap notes so work
  can resume cleanly later.
- Repo-local implementation detail belongs in the owning repo; cross-repo
  product flow belongs here.

## Phase Overview

### Phase 1: SDK And Integration Maturity

Primary repo:

- `xian-py`

Supporting repos:

- `xian-docs-web`

Outcome:

- the SDK becomes a strong application integration surface, not just a node
  helper

### Phase 2: Template-Driven Network Creation

Primary repos:

- `xian-configs`
- `xian-cli`
- `xian-stack`

Supporting repos:

- `xian-docs-web`
- `xian-deploy`

Outcome:

- purposeful network templates become the default way to start a Xian network

### Phase 3: Monitoring, Control, And Recovery

Primary repos:

- `xian-stack`
- `xian-cli`
- `xian-deploy`

Supporting repos:

- `xian-docs-web`

Outcome:

- running and operating a Xian node feels predictable and observable

### Phase 4: Reference Solution Packs

Primary repos:

- `xian-docs-web`
- `xian-py`
- `xian-configs`
- `xian-stack`

Outcome:

- Xian is demonstrated through concrete backend-oriented use cases instead of
  generic toy examples

## Phase 1: SDK And Integration Maturity

### Goal

Make `xian-py` feel like a serious SDK for services, workers, automation
scripts, and backend applications.

### Progress

- done: typed node status reads
- done: block watchers using raw node RPC with resume by height
- done: event watchers using indexed BDS reads with stable `after_id` cursor
- done: explicit SDK config objects and retry/resource policy
- done: higher-level SDK application helper layer
- done: service integration examples
- next: define the first template-driven network slice

### Deliverables

#### 1. Watchers And Subscriptions

Add first-class SDK support for:

- waiting for transactions cleanly
- polling new blocks with resume support
- watching contract events with cursor/height continuation
- reconnect and retry behavior for long-running consumers

This can start as polling-based if that keeps the implementation reliable and
simple.

#### 2. Explicit Client Configuration

Add config objects for:

- transport and timeout behavior
- retry/backoff policy
- tx submission policy
- watcher/subscription behavior

The current client methods work, but they still expose too much behavior
through loose parameters and defaults.

#### 3. Higher-Level Application Helpers

Add a small application-facing layer above the raw client surface.

Examples:

- `ContractClient`
- `EventClient`
- `HistoryClient`
- `TokenClient`

These should remove repetitive boilerplate without hiding the underlying
network model.

#### 4. Integration Examples

Provide examples for:

- a Python API service
- a background worker consuming chain events
- an admin or automation job

These examples should show how Xian fits into ordinary software workflows.

### Recommended Order

1. watchers and subscriptions
2. config objects and retry policy
3. higher-level application helper layer
4. service integration examples

### Exit Criteria

Phase 1 is considered complete when:

- the SDK supports long-running block and event consumers
- client behavior is configurable through explicit config objects
- common application patterns have thin helper clients
- the repo includes realistic examples for:
  - an API service
  - an event-driven worker
  - an admin or automation job
- `xian-docs-web` documents the resulting SDK surface

### Docs Work Required

Update `xian-docs-web` at each step:

- `tools/xian-py.md`
- `tools/index.md`
- architecture or integration pages if the SDK surface changes materially

Also maintain `xian-py/docs/SDK_REVIEW_BACKLOG.md` as slices are completed.

## Phase 2: Template-Driven Network Creation

### Goal

Make network creation feel intentional and productized instead of assembled
from lower-level pieces.

### Progress

- done: define canonical starter template names and intent
- done: add the initial canonical template catalog in `xian-configs`
- done: expose `network template list/show` and `--template` in `xian-cli`
- done: flow template defaults into created node profiles, including
  monitoring
- done: align the `xian-stack` backend contract with template-driven
  monitoring state
- done: add unified local operator status summary in `xian-cli`
- done: add endpoint discovery in `xian-cli` and the `xian-stack` backend
- done: update template-aware operator docs and examples
- next: begin the deeper Phase 3 doctor / health-check slice

### Initial Template Set

#### `single-node-dev`

- one node
- dashboard on
- BDS off by default
- fast local contract iteration

#### `single-node-indexed`

- one node
- BDS on
- dashboard on
- Prometheus on
- useful for backend integration development

#### `consortium-3`

- three validators
- conservative defaults
- monitoring enabled
- snapshot and state-sync guidance

#### `public-network-starter`

- multi-node starter shape
- stricter operational defaults
- monitoring and recovery enabled by default
- positioned for public network experimentation

#### `embedded-backend`

- positioned as a decentralized backend for an application
- one or few authorities depending on profile
- BDS on
- integration-friendly defaults

### Repo Responsibilities

#### `xian-configs`

- canonical manifests and settings per template

#### `xian-cli`

- template selection and creation UX
- commands such as `xian network create --template ...`

#### `xian-stack`

- runtime defaults and compose/preset behavior aligned to templates

#### `xian-deploy`

- deployment playbooks aligned to template classes

### Recommended Order

1. define canonical template names and intent
2. add manifests in `xian-configs`
3. expose template-driven creation in `xian-cli`
4. align `xian-stack` presets and defaults
5. add `xian-deploy` support where it materially differs by template

### Docs Work Required

Update `xian-docs-web` as template support lands:

- node/network setup pages
- CLI pages
- deployment/operator guidance

## Phase 3: Monitoring, Control, And Recovery

### Goal

Make it easy to understand what a node is doing and what to do when it is not
healthy.

### Progress

- done: add unified local operator status summary in `xian-cli`
- done: add explicit endpoint discovery in `xian-cli` and `xian-stack`
- done: make `doctor` perform live health checks by default
- done: keep offline preflight available via `--skip-live-checks`
- done: add dedicated machine-readable health commands in `xian-stack` and
  `xian-cli`
- done: expose state-sync readiness and snapshot-bootstrap visibility in the
  operator surface
- done: standardize template-aware monitoring defaults through explicit
  `operator_profile` and `monitoring_profile` metadata
- done: deepen service-node diagnostics around BDS queue, spool, lag, and
  database state
- done: tighten state-sync and snapshot recovery flows around concrete operator
  runbooks and remote deployment checks
- next: start the first reference solution pack on top of the completed golden
  path foundations

### Deliverables

#### 1. Unified Status Commands

Add or improve commands so operators can quickly see:

- node up/down state
- current height
- catching-up state
- peers
- BDS enabled/disabled and lag
- dashboard/metrics endpoints

#### 2. Doctor / Health Checks

Add a stronger diagnostic surface for:

- RPC reachability
- CometBFT health
- disk pressure
- spool health
- Postgres/BDS health
- snapshot and state-sync readiness

#### 3. Endpoint Discovery

Add one obvious way to print the useful local endpoints for a running stack.

Examples:

- dashboard URL
- metrics URL
- Prometheus URL
- Grafana URL
- BDS/GraphQL status if enabled

#### 4. Monitoring Presets

Standardize monitoring defaults by template:

- local dev
- indexed local backend
- consortium
- public network starter

### Repo Responsibilities

#### `xian-stack`

- local stack status
- doctor
- endpoint discovery
- monitoring defaults and presets

#### `xian-cli`

- higher-level operator commands where appropriate

#### `xian-deploy`

- remote deployment and operational checks

### Docs Work Required

Keep `xian-docs-web` current for:

- monitoring layers
- operator workflows
- recovery and troubleshooting

## Phase 4: Reference Solution Packs

### Goal

Prove the product thesis with realistic examples that are smaller than full
products but more meaningful than toy demos.

### Progress

- done: define the canonical solution-pack set and the first-pack scope
- done: implement the Credits Ledger Pack across shared assets, SDK examples,
  and public docs
- done: define the Registry / Approval Pack scope
- done: implement the Registry / Approval Pack across shared assets, SDK
  examples, and public docs
- done: define the Workflow Backend Pack scope
- done: implement the Workflow Backend Pack across shared assets, SDK
  examples, and public docs
- done: choose the Credits Ledger Pack as the first deeper reference
  application slice
- done: turn the Credits Ledger Pack into a fuller reference application with
  a projected read model and richer service flow
- done: choose Registry / Approval as the second deeper reference application
  slice
- done: turn the Registry / Approval Pack into a fuller reference application
  with an event-driven hydrated read model
- next: decide how far to deepen the Workflow Backend Pack as the third deeper
  reference-app slice

### Initial Candidate Packs

#### Credits Ledger Pack

- token or credits contract
- Python service using `xian-py`
- event watcher
- indexed read examples
- deeper reference-app direction:
  - projected activity and summary read model outside the chain
  - richer API service that combines authoritative chain reads and projected
    application reads
  - a resumable projector worker that rebuilds the projection from indexed
    events

#### Registry / Approval Pack

- registry contract
- approval or governance layer
- Python admin flow
- monitoring and recovery guidance
- deeper reference-app direction:
  - projected proposal and record views outside the chain
  - event-driven projection that uses indexed events as triggers and
    authoritative contract reads as hydration
  - richer API service for pending approvals, records, and audit activity

#### Workflow Backend Pack

- state-machine style contract
- Python worker consuming events
- API service reading indexed state and history

### Output Shape

Each pack should explain:

- why Xian fits this problem
- how to start the network
- how the app talks to it
- how to monitor and recover it

## Recommended Immediate Order

### Do Now

1. mature `xian-py` with watchers/subscriptions
2. add SDK config objects and retry/resource policies
3. define and implement the first network template set
4. add unified local stack status and endpoint discovery

### Do Soon After

1. add higher-level SDK application helpers
2. add stronger doctor/health workflows
3. align `xian-deploy` with the initial template set
4. build the first reference solution pack

### Do Later

1. broader multi-account adoption work
2. a future Xian VM or bytecode implementation
3. deeper throughput-focused optimization beyond obvious product needs

## Current Next Action

With the initial solution-pack set in place:

1. decide the Workflow Backend deeper reference-app scope
2. keep the docs and roadmap updated as that slice lands
3. only add more pack variety after the deeper reference-app pattern is proven
