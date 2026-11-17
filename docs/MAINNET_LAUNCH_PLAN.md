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

The draft bundle starts from one bootstrap validator in
`selection_mode = "manual"` with `max_validators = 13` and equal CometBFT
power: governance adds validators with `add_member`, which requires
`min_self_bond = 100000` and `min_total_bond = 500000` XIAN. A later switch to
`auto_top_n`/`hybrid` (one `update_policy` vote, only with a full bonded set)
ranks validators by `self_bond + total_delegated` and admits newcomers within
`max_active_set_churn = 1` and `max_new_power_bps = 2000` per rebalance.
Validators absent from 500 consecutive commits are jailed for downtime
(no slash; self-unjail after 24 hours); a chain halted by a third or more of
offline power restarts through the recovery genesis (docs-web operator
runbook, Halt Recovery). Until the set has four validators each newcomer holds
a third or more of the power: approve only candidates whose node is already
synced with its consensus key.

The mainnet manifest enables the chain `zk` runtime feature, but the privacy
catalog intentionally has no approved proving artifacts until ceremony-derived
artifacts are imported and checksum-pinned.

## Consensus And Bootstrap Gate

The fresh-chain baseline is unmodified upstream CometBFT 0.40.0, at source
commit `0880b4d378f347ab16e54ec677ff50d803f37d62`, with peer-to-peer application
state sync disabled. Pin the upstream version and archive hash alongside the
matching Xian application and immutable node image digests. Expected
CLI/deployment metadata is not attestation of an arbitrary installed binary.
Do not swap a consensus-sensitive backend into an existing development or live
chain without a separately reviewed network upgrade.

The current mainnet and testnet manifests remain `draft-rehearsal` recipes with
`local_build` images. Their intended CometBFT source recipe does not attest any
older registry image. Publish and accept the matching source train and image
digests before changing either network to a finalized registry-backed manifest.

Before accepting the release, require a fresh multi-validator rehearsal from
those exact inputs. Exercise full replay from genesis and verified full
node-store snapshot bootstrap, including historical evidence from before the
snapshot checkpoint, pruning boundaries, interrupted restore and restart, and
rejection of missing or inconsistent consensus stores. Record the accepted
chain identity, genesis hash, checkpoint, archive checksum and publisher trust
material. An application-state snapshot alone is not a supported bootstrap.

Genesis must commit an evidence duration covering the seeded unbonding period
plus one day (at least 15 days for the draft 14-day mainnet policy), preserving
larger explicit settings. Governance increases raise the committed target while
the effective duration grows no faster than elapsed committed time; reductions
must not shrink it. Rehearse increases, reductions and restart/replay against
the effective block-age window as well as the duration schedule. Preserve the
evidence byte cap and conservatively retain the height history required by up
to two rooted security-checkpoint epochs, including during pruning and
full-store snapshot bootstrap. These are acceptance requirements, not a
statement that the final release gates have passed. Operator details live
in `xian-docs-web/node/configuration.md` and `node/pruning.md`.

## Launch Inputs

The draft allocation has an unresolved custody blocker: `team_lock` receives
66,666,666.60 tokens (60% of supply), but the canonical bundle deploys no contract
at that name and it is not a signing account. Final genesis must use an accepted
custody account or deploy a reviewed vault with explicitly accepted owners and
quorum. Do not treat the draft allocation as spendable or launch-ready until
that choice is resolved and rehearsed.

Before final genesis, the launch owner must publish or accept:

- final allocation file and generated `contracts_mainnet.json`
- release manifest with pinned repo SHAs, image digests, and package versions
- stable non-beta release tags for every released package/repo in the launch train
- signed genesis hash and reproducible command used to generate it; the hash
  is the manifest's `genesis_sha256` (SHA-256 of the `config/genesis.json`
  that `xian node init` installs), which nodes enforce on init
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
8. Regenerate genesis, pin its hash as `genesis_sha256` in
   `xian-configs/networks/mainnet/manifest.json` (with `genesis_build.status`
   no longer `draft-rehearsal`, `validate-manifests.py` refuses a missing or
   stale pin), sign that hash, publish the operator bundle (it carries the pin),
   and publish the signed hash through a channel separate from the bundle.

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
