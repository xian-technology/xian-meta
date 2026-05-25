# Examples

This file defines the current reference example set for Xian. An example is an
opinionated, repeatable backend pattern that proves Xian works as a
Python-first decentralized backend for real application workflows.

The machine-readable source of truth for installable starter flows lives in
`xian-configs/examples/<name>/example.json`. Public walkthroughs live in
`xian-docs-web/examples/`.

## Example Requirements

An example should have:

- one clear use case
- one small contract set or optional contract pack
- one recommended local network template
- one Python integration path
- one operator/recovery story when it affects node operation
- one machine-readable starter manifest
- one public docs walkthrough

An example should not become a customizable framework. If the use case needs a
full product, the example should stay as the reusable starter path and the
product should live elsewhere.

## Current Set

### Credits Ledger

Use case:

- programmable internal credits, balances, issuance, transfers, burns, and
  auditability

Canonical assets:

- `xian-configs/examples/credits-ledger/example.json`
- `xian-configs/examples/credits-ledger/contracts/credits_ledger.s.py`
- `xian-docs-web/examples/credits-ledger.md`

Recommended template:

- `single-node-indexed`

The deeper reference-app path is implemented in `xian-py/examples`, with an
admin job, API service, projector, and local read model.

### DEX Demo

Use case:

- deterministic deployment of the canonical Xian AMM contracts under known
  names for wallets, the DEX web app, event automation, and integration tests

Canonical assets:

- `xian-configs/examples/dex-demo/example.json`
- `xian-configs/contract-packs/dex/contract-pack.json`
- `xian-configs/contract-packs/dex/contract-bundle.json`
- `xian-docs-web/examples/dex-demo.md`

Recommended template:

- `single-node-indexed`

The active DEX codebase remains `xian-dex`; `xian-configs/contract-packs/dex`
is the hash-pinned deployable contract pack snapshot.

### Registry / Approval

Use case:

- shared records that must be proposed, reviewed, approved, revoked, or updated
  by multiple parties

Canonical assets:

- `xian-configs/examples/registry-approval/example.json`
- `xian-configs/examples/registry-approval/contracts/registry_records.s.py`
- `xian-configs/examples/registry-approval/contracts/registry_approval.s.py`
- `xian-docs-web/examples/registry-approval.md`

Recommended template:

- `single-node-indexed`

The deeper reference-app path is implemented in `xian-py/examples`, with an
admin job, API service, projector, hydrated projections, and approval activity
views.

### Workflow Backend

Use case:

- shared state-machine workflows with explicit transitions, event-driven
  workers, and durable history

Canonical assets:

- `xian-configs/examples/workflow-backend/example.json`
- `xian-configs/examples/workflow-backend/contracts/job_workflow.s.py`
- `xian-docs-web/examples/workflow-backend.md`

Recommended template:

- `single-node-indexed`

The deeper reference-app path is implemented in `xian-py/examples`, with an
admin job, API service, processor worker, projector worker, queue projections,
and activity views.

### x402 Exact

Use case:

- fixed-price HTTP 402 paid API requests settled through native Xian token
  contracts

Canonical assets:

- `xian-configs/examples/x402-exact/example.json`
- `xian-configs/examples/x402-exact/contracts/x402_settlement.s.py`
- `xian-py/examples/x402_exact/README.md`

Recommended template:

- `single-node-indexed`

The deeper reference-app path is implemented in `xian-py/examples`, with a
settlement deployment job, paid FastAPI resource server, optional facilitator
service, and buyer client.

## Boundary

`xian-meta` owns the cross-repo definition of what belongs in the example set.
The implementation lives in the owning repos:

- contracts and starter manifests: `xian-configs`
- Python examples and reusable projection helpers: `xian-py`
- public walkthroughs: `xian-docs-web`
- runtime/bootstrap consumers: `xian-cli` and `xian-stack`
