# Solution Packs

## Purpose

This file defines the canonical reference solution-pack set for the Xian
product direction.

These packs are not meant to be polished end-user products. They are meant to
prove that Xian works as a Python-first decentralized backend for real
application patterns.

Each pack should stay opinionated, narrow, and repeatable.

## What A Solution Pack Must Include

Every solution pack should ship with:

- one clear use case
- one small contract set
- one recommended local network template
- one recommended remote/operator template
- one Python integration surface
- one operator/recovery story
- one docs walkthrough

It should not try to be a customizable framework.

## Pack Set

### 1. Credits Ledger Pack

#### Use Case

An application needs a programmable internal ledger for credits, balances,
issuance, transfers, burns, and auditability.

Examples:

- platform credits
- community points
- API usage credits
- marketplace balances
- partner settlement units

#### Why Xian Fits

- easy contract logic
- easy Python integration
- strong event and history surface
- straightforward operator story with BDS-enabled reads

#### Story

A platform runs a small Xian network and uses it as the authoritative ledger
for application credits, while keeping the rest of its relational application
state off-chain.

#### Recommended Operator Paths

- local: `single-node-indexed`
- remote: `embedded-backend`

#### Expected Components

- credits-ledger contract with issuer/operator controls
- Python API-service example
- Python event-worker example
- Python admin/bootstrap example
- docs walkthrough covering deploy, integration, monitoring, and recovery

### 2. Registry / Approval Pack

#### Use Case

A network needs a shared registry of records that must be proposed, reviewed,
approved, revoked, or updated by multiple parties.

Examples:

- partner/vendor registry
- certificate or credential registry
- allowlist / permission registry
- consortium member record system

#### Why Xian Fits

- shared state across organizations
- programmable approvals
- clean auditability
- easy Python admin/service integration

#### Story

Several parties share one registry. One party proposes a change, another
approves it, and the network records the full history with a thin Python admin
and service layer around it.

#### Recommended Operator Paths

- local: `single-node-indexed`
- remote: `consortium-3`

#### Expected Components

- registry contract
- approval policy contract
- Python admin/service flow
- monitoring and recovery walkthrough

## Second Pack Scope: Registry / Approval

The second implementation slice should stay narrow and complete enough to be a
real shared-state pattern.

It should include:

- a reusable registry contract asset in `xian-configs`
- a reusable approval-policy contract asset in `xian-configs`
- pack-specific integration examples in `xian-py`
- a public docs walkthrough in `xian-docs-web`
- alignment with the existing `single-node-indexed` and `consortium-3`
  operator flows

It should not need:

- a full UI
- generalized on-chain governance
- large role-management subsystems
- protocol changes

## Completion Criteria For The Registry / Approval Pack

The second pack is considered done when:

- the registry and approval contract assets exist in a stable repo location
- the SDK examples show bootstrap, proposal, approval, and event-consumption
  patterns
- the docs explain the use case, deployment path, approval path, and
  monitoring/recovery path
- the roadmap and docs log are updated so the third pack can start cleanly

### 3. Workflow Backend Pack

#### Use Case

An application needs a shared state machine with explicit transitions,
event-driven workers, and durable history.

Examples:

- order workflow
- claims processing
- dispute workflow
- ticket lifecycle
- shipment or fulfillment tracking

#### Why Xian Fits

- explicit workflow rules on-chain
- Python workers around it
- event-driven integration
- history and audit trail built in

#### Story

A backend service writes workflow actions to Xian, workers react to events, and
user-facing systems query current state and history through indexed reads.

#### Recommended Operator Paths

- local: `single-node-indexed`
- remote: `embedded-backend` or `consortium-3`, depending on the trust model

#### Expected Components

- workflow state-machine contract
- Python API service
- Python worker consuming events
- indexed-read examples

## Third Pack Scope: Workflow Backend

The third implementation slice should stay narrow and complete enough to show
Xian as a decentralized backend coordination layer.

It should include:

- a reusable workflow state-machine contract asset in `xian-configs`
- pack-specific integration examples in `xian-py`
- a public docs walkthrough in `xian-docs-web`
- alignment with the existing `single-node-indexed` and `embedded-backend`
  operator flows

The concrete story for `v1` is a job-style workflow backend:

- clients submit workflow items
- workers claim them for processing
- workers complete or fail them
- off-chain systems consume the emitted events and current state

It does not need:

- a full UI
- generalized BPM/workflow tooling
- a second governance/approval layer
- protocol changes

## Completion Criteria For The Workflow Backend Pack

The third pack is considered done when:

- the workflow contract asset exists in a stable repo location
- the SDK examples show bootstrap, service submission/query, and worker
  processing patterns
- the docs explain the use case, deployment path, integration path, and
  monitoring/recovery path
- the roadmap and docs log are updated to mark the initial pack set complete

## Recommended Order

Implement the packs in this order:

1. Credits Ledger Pack
2. Registry / Approval Pack
3. Workflow Backend Pack

This order is intentional:

- Credits Ledger validates the core golden path with minimal domain complexity.
- Registry / Approval validates shared multi-party state and approvals.
- Workflow Backend validates the broader decentralized-backend thesis.

## First Pack Scope: Credits Ledger

The first implementation slice should stay narrow and complete enough to be
real.

It should include:

- a reusable credits-ledger contract bundle in `xian-configs`
- pack-specific integration examples in `xian-py`
- a public docs walkthrough in `xian-docs-web`
- alignment with the existing `single-node-indexed` and
  `embedded-backend` operator flows

It does not need:

- a full UI
- a separate reference application repo
- protocol changes
- new runtime features

## Completion Criteria For The Credits Ledger Pack

The first pack is considered done when:

- the contract assets exist in a stable repo location
- the SDK examples show bootstrap, service, and worker patterns
- the docs explain the use case, deployment path, integration path, and
  monitoring/recovery path
- the roadmap and docs log are updated so the next pack can start cleanly

## First Deeper Reference-App Slice: Credits Ledger

After the initial three-pack set is complete, the first deeper reference-app
slice should still build on Credits Ledger.

That deeper slice should demonstrate:

- the chain as the authoritative credits ledger
- a local projected read model outside the chain
- a resumable projector that rebuilds projections from indexed events
- an API service that combines authoritative chain reads and projected
  application reads

It still does not need:

- a separate frontend
- a separate repo
- new protocol features

## Second Deeper Reference-App Slice: Registry / Approval

After the Credits Ledger reference-app slice, the next deeper slice should
build on Registry / Approval.

That deeper slice should demonstrate:

- indexed events as workflow triggers
- authoritative contract reads used to hydrate richer proposal and record
  projections
- a resumable local read model for pending approvals, registry records, and
  audit activity
- an API service that serves both on-chain reads and projected workflow views

It still does not need:

- a separate frontend
- a separate repo
- generalized governance machinery
- new protocol features

## Third Deeper Reference-App Slice: Workflow Backend

After the Registry / Approval reference-app slice, the next deeper slice built
on Workflow Backend.

That deeper slice demonstrates:

- separate processor and projector workers
- indexed events as workflow and projection triggers
- authoritative contract reads used to hydrate richer item projections
- a resumable local read model for queue state, item catalogs, and activity
- an API service that serves both on-chain reads and projected workflow views

It still does not need:

- a separate frontend
- a separate repo
- generalized workflow tooling
- new protocol features
