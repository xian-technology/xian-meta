# Mainnet Launch Plan

The current codebase has no active public testnet or public mainnet. A draft
mainnet rehearsal manifest now exists in `xian-configs` for the new network:

- network name: `mainnet`
- chain ID: `xian-mainnet-1`
- config path: `../xian-configs/networks/mainnet/manifest.json`

This page is still a launch checklist, not a launch announcement. Do not add
public RPC defaults, public peer sets, public snapshot URLs, or product defaults
that imply this network is live until the final gates below are closed.

## Prepared Config State

`xian-configs` now owns the draft mainnet assets needed for dry-runs:

- `contracts/contracts_mainnet.json`
- `contracts/mainnet_allocations.json`
- `networks/mainnet/manifest.json`
- `networks/mainnet/privacy/artifacts.json`

The draft bundle starts from one bootstrap validator and uses
`selection_mode = "auto_top_n"` with `max_validators = 25`. Validators are
ranked by `self_bond + total_delegated`; CometBFT power is equal per active
validator.

The mainnet manifest enables the chain `zk` runtime feature, but the privacy
catalog intentionally has no approved proving artifacts until ceremony-derived
artifacts are imported and checksum-pinned.

## Launch Inputs

Before final genesis, the launch owner must publish or accept:

- final allocation file and generated `contracts_mainnet.json`
- release manifest with pinned repo SHAs, image digests, and package versions
- stable non-beta release tags for every released package/repo in the launch train
- signed genesis hash and reproducible command used to generate it
- initial bootstrap validator public key and contact process
- seed nodes and persistent-peer policy
- snapshot publication policy and restore validation command
- public RPC, GraphQL, dashboard, and explorer policy
- monitoring, alerting, rollback, and emergency governance process
- operator onboarding runbook and dry-run schedule
- ZK ceremony transcript/package hash and accepted registry manifests, or an
  explicit decision to launch with the mainnet privacy catalog empty

## Rehearsal Order

1. Generate and validate the draft mainnet genesis from `xian-configs`.
2. Package an operator bundle with a placeholder or rehearsal bootstrap seed.
3. Start a one-node rehearsal using the materialized mainnet genesis.
4. Run localnet and multi-node E2E from the exact release manifest.
5. Run a public-style test network with real seed discovery, peer churn,
   validator onboarding, snapshots, and restore drills.
6. Freeze the release candidate and repeat the rehearsal without code changes.
7. Replace the draft allocation, seed, image pins, and release manifest with
   final launch values.
8. Regenerate genesis, sign the genesis hash, and publish the operator bundle.

## Required Artifacts

- `xian-configs/networks/mainnet/` manifest
- materialized genesis file and signed hash record
- validator onboarding packet
- operator runbook
- snapshot restore runbook
- public endpoint inventory
- incident response runbook
- release manifest that pins every shipping repo and package version
- ZK ceremony/import record for any approved shielded proving artifacts

## Release Hygiene Before Upversion

Do not start the stable-version bump until these checks are complete:

- all `uv.lock` files in release-participating Python repos are current
- `xian-configs/scripts/validate-manifests.py` passes
- `xian-configs/scripts/sync-mainnet-allocations.py --check` passes
- mainnet operator bundle packaging succeeds from the checked-in manifest
- `xian-stack` release manifest and node image pins are refreshed after the
  final repo commits
- packages that publish extras keep the expected dependency split, including
  compile/zk/native extras where applicable
- docs that mention operator-visible mainnet behavior point to the new
  `xian-mainnet-1` launch plan rather than historical networks

## Guardrails

- Keep local defaults local: `http://127.0.0.1:26657` and explicit local chain
  IDs are acceptable examples.
- Use `xian-mainnet-1` only for the new current-codebase launch.
- Do not reuse historical public network identifiers for this codebase.
- Do not treat a green localnet as a public-network rehearsal unless peer
  discovery, snapshots, validator onboarding, and public endpoint policy were
  exercised.
- Do not publish mainnet shielded proving artifacts unless they come from the
  accepted ceremony/import process.
