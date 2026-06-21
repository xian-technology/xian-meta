# Future Mainnet Launch Plan

The current codebase has no active public testnet or public mainnet. Do not add
a `mainnet` network manifest, public chain ID, public RPC default, public peer
set, or public snapshot URL until the launch inputs below are ready.

This page is the planning checklist for the future public network that will run
the current codebase. It is not a launch announcement and it does not define a
chain ID.

## Launch Inputs

Before a `networks/mainnet` manifest is created in `xian-configs`, the launch
owner should publish:

- final chain ID and network name
- release manifest with pinned repo SHAs, images, and package versions
- genesis ceremony process and signed genesis hash
- initial validator roster, public keys, voting power, and contact process
- seed nodes and persistent-peer policy
- snapshot publication policy and restore validation command
- public RPC, GraphQL, dashboard, and explorer policy
- monitoring, alerting, rollback, and emergency governance process
- operator onboarding runbook and dry-run schedule

## Rehearsal Order

1. Create a private launch rehearsal manifest in `xian-configs`.
2. Run localnet and multi-node E2E from the exact release manifest.
3. Run a public-style test network with real seed discovery, peer churn,
   validator onboarding, snapshots, and restore drills.
4. Freeze the release candidate and repeat the rehearsal without code changes.
5. Create `networks/mainnet` only after the release candidate, validator set,
   genesis ceremony, and operator runbook are all accepted.

## Required Artifacts

- `xian-configs/networks/mainnet/` manifest
- genesis file and signed hash record
- validator onboarding packet
- operator runbook
- snapshot restore runbook
- public endpoint inventory
- incident response runbook
- release manifest that pins every shipping repo and package version

## Guardrails

- Keep local defaults local: `http://127.0.0.1:26657` and explicit local chain
  IDs are acceptable examples.
- Use placeholders such as `<target-chain-id>` in docs before launch details
  are final.
- Do not reuse historical public network identifiers for the current codebase.
- Do not treat a green localnet as a public-network rehearsal unless peer
  discovery, snapshots, validator onboarding, and public endpoint policy were
  exercised.
