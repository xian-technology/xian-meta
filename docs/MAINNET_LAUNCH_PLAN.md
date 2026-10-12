# Mainnet Launch Plan

The current codebase has no active public testnet or public mainnet. A draft
mainnet rehearsal manifest now exists in `xian-configs` for the new network:

- network name: `mainnet`
- chain ID: `xian-mainnet-1`
- config path: `../xian-configs/networks/mainnet/manifest.json`

This page is still a launch checklist, not a launch announcement. Do not add
public RPC defaults, public peer sets, public snapshot URLs, or product defaults
that imply this network is live until the final gates below are closed.

## Fresh-chain migration scope

The accepted direction is a new chain built from the current codebase, with
legacy-chain funds represented by a reviewed new genesis allocation. This is
not an in-place upgrade of the old chain or the running localnet. `team_lock`
is not required on the new network; a new contract will be designed separately.
The existing localnet's missing lock is an audit observation, not a requirement
to recreate that contract for launch.

The canonical allocation is empty and marked `pending_snapshot`. Genesis
construction refuses it. The currency metadata operator is `governance`; the
old team allocation formula and permit authorizer are removed. No final amounts,
beneficiaries or contract custody decisions are inferred.

Follow the [snapshot-to-genesis specification](SNAPSHOT_GENESIS_MIGRATION.md).
`xian network convert-legacy-balances` converts legacy BDS export rows without
importing allowances. `xian network migrate-balances` reconciles native balances,
preserves exact account identifiers, and generates a separate current-source
bundle with closed registry policy. Nonzero contract holdings require explicit
conserved dispositions; undeployed destination contract names are rejected.
Selected contract constructor/custody decisions still need review.

Before final genesis, accept the source cutoff, complete snapshot, exact amounts,
contract beneficiaries and pinned release artifacts. Rehearse the resulting
bundle with funded old-key accounts, final fees, five validators, restarts,
verified hybrid backups and recovery. No old-chain upgrade or key conversion is
required to receive balances. A public live-state sample is not a final snapshot.

The independent review, device/storage testing and release gates below still
apply. New-chain genesis does not make an unenrolled Ed25519 account quantum
resistant or give an old seed the new active/recovery secrets.

## Prepared Config State

`xian-configs` now owns the draft mainnet assets needed for dry-runs:

- `contracts/contracts_mainnet.json`
- `contracts/mainnet_allocations.json`
- `networks/mainnet/manifest.json`
- `networks/mainnet/privacy/artifacts.json`

The draft bundle starts from one bootstrap validator and uses
`selection_mode = "auto_top_n"` with `max_validators = 13`. Validators are
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

## Cryptographic Readiness

The [hybrid account authorization experiment](HYBRID_ACCOUNT_AUTH_EXPERIMENT.md)
defines a local-only byte contract and trusted-record boundary for evaluating
Ed25519 + ML-DSA-65. The subsequent
[account-registry integration](ACCOUNT_REGISTRY_PROTOCOL.md) adds an explicit
node wire format, consensus-backed authorization, and identity-preserving local
migration tests. Current source SDKs and wallets add verified active/recovery
backups, durable pending credentials, fresh-device recovery and cross-language
production-format checks. Enrollment is disabled in default networks. Independent
review, physical-device measurements and coordinated release remain activation
gates. The [custody recovery matrix](../../xian-js/docs/ACCOUNT_CUSTODY_REVIEW.md)
records local fault-injection findings and the remaining rehearsal requirements.
The isolated five-validator rehearsal now passes using pinned v0.39.3 CometBFT
sources: quorum loss, crash/restart, cold recovery and Python/JS restored spending
preserve the original identity and account state. The integration inventory also
covers service signers and image crypto dependencies. Repeat on the final release
artifacts; these checks do not constitute public-network activation.

Before enrollment, audit every selected and subsequently deployed contract's
authorization. Fresh-chain currency and stream contracts expose only direct
caller authorization; old permit gateways are removed. The historical
[deployed-contract audit](../../xian-stack/docs/DEPLOYED_CONTRACT_UPGRADE_PLAN.md)
remains evidence of the old deployment, not a patch plan for the new network.
The legacy x402 permit settlement example is retired; a new authenticated payment
profile requires separate design and validation before it can be supported.
Upgrade every validator/RPC before exposing the new wallet workflow. Older RPCs
without the explicit registry-absence encoding fail closed in the new custody
client; this is not a supported mixed-version wallet/RPC deployment.

Before freezing a release candidate, record an independent review of account
and validator signing, wallet custody, the bridge, and shielded proof boundaries.
Run adversarial signature-acceptance parity tests against rebuilt Python/native
admission and VM components. Runtime changes that tighten signature acceptance
must ship as a coordinated validator release, not a mixed-version rollout.

See [the quantum-resistance roadmap](QUANTUM_RESISTANCE_ROADMAP.md) for the
cross-repository priorities and acceptance gates beyond account custody.

Default account and validator signatures are Ed25519. Explicitly enrolled
registry accounts require Ed25519 AND ML-DSA-65. Groth16/BN254 shielded
proofs and Curve25519 SDK encryption also require separate post-quantum work;
wallet password hardening does not change those cryptographic assumptions.

The authentication release must close the following design, review, and
rehearsal gates before activation:

- a versioned account authorization envelope, independent of a fixed-length
  public-key-as-address representation
- a local Ed25519 + ML-DSA-65 prototype requiring both signatures, with both keys,
  algorithm identifiers, account, chain, and transaction bound into signing bytes
- authenticated key enrollment/rotation, downgrade prevention, recovery rules,
  and a migration rehearsal that completes before legacy keys become forgeable
- measured verification costs, signature bandwidth, mobile signing, deterministic
  parsing, transaction-size limits, and invalid-signature denial-of-service limits
- a separate CometBFT/validator/light-client upgrade design and inventory of
  bridge, release, genesis, administrative, and encrypted-message dependencies
- an independent shielded-proof migration decision; an account-signature upgrade
  does not justify describing the entire chain as post-quantum secure

These are release and activation gates. It does not activate a signature algorithm,
change genesis/network defaults, or authorize a public network launch.

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
