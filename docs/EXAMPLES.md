# Examples And Product Starters

This file defines the current reference example set for Xian. An example is a
small, repeatable backend pattern that proves Xian works as a Python-first
decentralized backend for real application workflows.

Example contract sources live beside the SDK example code that consumes them.
Product starter flows live in the owning product repo. Public walkthroughs live
in the owning SDK or product repo docs.

## Example Requirements

An example should have:

- one clear use case
- one small contract set or optional product dependency
- one recommended local network template
- one Python integration path
- one operator/recovery story when it affects node operation
- one public docs walkthrough

An example should not become a customizable framework. If the use case needs a
full product, the product should live in its own owning repo.

## Current Set

### Credits Ledger

Use case:

- programmable internal credits, balances, issuance, transfers, burns, and
  auditability

Canonical assets:

- `xian-py/examples/credits_ledger/contracts/credits_ledger.s.py`
- `xian-py/examples/credits_ledger/README.md`

Recommended template:

- `single-node-indexed`

The deeper reference-app path is implemented in `xian-py/examples`, with an
admin job, API service, projector, and local read model.

### DEX Demo

Use case:

- deterministic deployment of the canonical Xian AMM contracts under known
  names for wallets, the DEX web app, event automation, and integration tests

Canonical assets:

- `xian-dex/contract-bundle.json`
- `xian-dex/scripts/bootstrap_dex.py`
- `xian-docs-web/products/dex.md`

Recommended template:

- `single-node-indexed`

The active DEX codebase remains `xian-dex`; that repo owns the hash-pinned
deployable product snapshot and starter flow.

### Registry / Approval

Use case:

- shared records that must be proposed, reviewed, approved, revoked, or updated
  by multiple parties

Canonical assets:

- `xian-py/examples/registry_approval/contracts/registry_records.s.py`
- `xian-py/examples/registry_approval/contracts/registry_approval.s.py`
- `xian-py/examples/registry_approval/README.md`

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

- `xian-py/examples/workflow_backend/contracts/job_workflow.s.py`
- `xian-py/examples/workflow_backend/README.md`

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

- `xian-py/examples/x402_exact/contracts/x402_settlement.s.py`
- `xian-py/examples/x402_exact/README.md`

Recommended template:

- `single-node-indexed`

The deeper reference-app path is implemented in `xian-py/examples`, with a
settlement deployment job, paid FastAPI resource server, optional facilitator
service, and buyer client.

## Boundary

`xian-meta` owns the cross-repo definition of what belongs in the example set.
The implementation lives in the owning repos:

- network manifests, templates, and system contract bundles: `xian-configs`
- product contracts, bundles, apps, and starter flows: product repos
- Python examples and reusable projection helpers: `xian-py`
- public walkthroughs: `xian-docs-web`
- runtime/bootstrap consumers: `xian-cli` and `xian-stack`
