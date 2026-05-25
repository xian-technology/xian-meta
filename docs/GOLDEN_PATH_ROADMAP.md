# Golden Path Roadmap

## Status

Current cross-repo product roadmap.

The first golden-path foundation is implemented: SDK integration examples,
template-driven network creation, local and remote operator workflows, reference
examples, starter manifests, and whole-stack validation all exist. This file
now tracks the current direction rather than the completed implementation plan.

## Golden Path

The intended flow for a normal engineering team is:

1. choose a purposeful network template
2. start it locally or remotely
3. run an example or install a contract pack
4. integrate it from a Python service or worker
5. read state, history, and events through stable APIs
6. monitor, validate, recover, and upgrade the node predictably

The goal is not to expose every low-level switch first. The goal is to make the
common path obvious and boring.

## What Exists Now

- `xian-configs` owns canonical network templates, contract packs, and example
  starter manifests.
- `xian-cli` exposes network creation, node lifecycle, example inspection, and
  contract/contract pack helpers.
- `xian-stack` owns local runtime, monitoring, localnet, release, and
  validation harnesses.
- `xian-deploy` owns profile-driven remote operator playbooks.
- `xian-py` provides SDK clients, examples, and reusable projection helpers.
- `xian-docs-web` documents the public operator, contract, SDK, and example
  workflows.

## Current Priorities

### 1. Keep The Starter Flows Sharp

The current example set should remain small and high quality:

- Credits Ledger
- DEX Demo
- Registry / Approval
- Workflow Backend

New examples should be added only when they prove a distinct backend pattern.
Existing example manifests should stay installable through `xian-cli` and
validated by stack/localnet flows when they affect runtime behavior.

### 2. Tighten Remote Operations

Local workflows are now strong enough that the next product value is remote
operator clarity:

- profile-driven remote deploy flows that map cleanly to the same network templates
- health and recovery playbooks that match the local CLI mental model
- monitoring profiles that surface actionable node, BDS, and runtime state
- snapshot/state-sync guidance that is explicit about source of truth

### 3. Keep Validation Release-Grade

The serious validation paths are:

- `make localnet-e2e`
- `make localnet-parallel-e2e`
- `make release-safety`

The docs source of truth for these flows is
`xian-docs-web/node/localnet-e2e.md`. `xian-meta/docs/LOCALNET_E2E_RUNBOOK.md`
keeps only the cross-repo pointer.

### 4. Defer Protocol Expansion Until It Serves A Product Path

VM work, multi-account support, privacy hardening, parallel execution, and
protocol-level upgrades are valuable, but they should stay tied to clear
product or operator needs. Avoid adding platform surface only because it is
technically interesting.

## Docs Discipline

When a roadmap item lands:

- update the public docs if the user-facing workflow changed
- update the owning repo's `docs/BACKLOG.md` if follow-up work remains
- remove completed implementation plans instead of preserving stale history
- keep this roadmap focused on current direction, not progress logs
