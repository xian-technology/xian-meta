# Solutions

This file defines the current reference solution set for Xian. A solution is an
opinionated, repeatable backend pattern that proves Xian works as a
Python-first decentralized backend for real application workflows.

The machine-readable source of truth for installable starter flows lives in
`xian-configs/solutions/<name>/solution.json`. Public walkthroughs live in
`xian-docs-web/solutions/`.

## Solution Requirements

A solution should have:

- one clear use case
- one small contract set or module bundle
- one recommended local network template
- one recommended remote/operator template
- one Python integration path
- one operator/recovery story
- one machine-readable starter manifest
- one public docs walkthrough

A solution should not become a customizable framework. If the use case needs a
full product, the solution should stay as the reusable starter path and the
product should live elsewhere.

## Current Set

### Credits Ledger

Use case:

- programmable internal credits, balances, issuance, transfers, burns, and
  auditability

Canonical assets:

- `xian-configs/solutions/credits-ledger/solution.json`
- `xian-configs/solutions/credits-ledger/contracts/credits_ledger.s.py`
- `xian-docs-web/solutions/credits-ledger.md`

Recommended operator paths:

- local: `single-node-indexed`
- remote: `embedded-backend`

The deeper reference-app path is implemented in `xian-py/examples`, with an
admin job, API service, projector, and local read model.

### DEX Demo

Use case:

- deterministic deployment of the canonical Xian AMM contracts under known
  names for wallets, the DEX web app, event automation, and integration tests

Canonical assets:

- `xian-configs/solutions/dex-demo/solution.json`
- `xian-configs/modules/dex/module.json`
- `xian-configs/modules/dex/contract-bundle.json`
- `xian-docs-web/solutions/dex-demo.md`

Recommended operator paths:

- local: `single-node-indexed`
- remote: `consortium-3`

The active DEX codebase remains `xian-dex`; `xian-configs/modules/dex` is the
hash-pinned deployable module snapshot.

### Registry / Approval

Use case:

- shared records that must be proposed, reviewed, approved, revoked, or updated
  by multiple parties

Canonical assets:

- `xian-configs/solutions/registry-approval/solution.json`
- `xian-configs/solutions/registry-approval/contracts/registry_records.s.py`
- `xian-configs/solutions/registry-approval/contracts/registry_approval.s.py`
- `xian-docs-web/solutions/registry-approval.md`

Recommended operator paths:

- local: `single-node-indexed`
- remote: `consortium-3`

The deeper reference-app path is implemented in `xian-py/examples`, with an
admin job, API service, projector, hydrated projections, and approval activity
views.

### Workflow Backend

Use case:

- shared state-machine workflows with explicit transitions, event-driven
  workers, and durable history

Canonical assets:

- `xian-configs/solutions/workflow-backend/solution.json`
- `xian-configs/solutions/workflow-backend/contracts/job_workflow.s.py`
- `xian-docs-web/solutions/workflow-backend.md`

Recommended operator paths:

- local: `single-node-indexed`
- remote: `embedded-backend` or `consortium-3`, depending on the trust model

The deeper reference-app path is implemented in `xian-py/examples`, with an
admin job, API service, processor worker, projector worker, queue projections,
and activity views.

## Boundary

`xian-meta` owns the cross-repo definition of what belongs in the solution set.
The implementation lives in the owning repos:

- contracts and starter manifests: `xian-configs`
- Python examples and reusable projection helpers: `xian-py`
- public walkthroughs: `xian-docs-web`
- runtime/bootstrap consumers: `xian-cli` and `xian-stack`
