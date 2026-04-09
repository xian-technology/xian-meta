# Privacy Asset Stack Follow-ups

Status: deferred follow-up note

This note captures what is still missing after the current shielded-note token,
`xian-zk` wallet/tooling, encrypted payload delivery path, exact-withdraw
support, and random deployment-bundle generator landed across the main repos.

This is not the place to restate the whole architecture. The architecture note
already exists in `REAL_PRIVACY_TOKEN_ARCHITECTURE.md`. This file is the short
cross-repo list of what is still needed before Xian can call the privacy asset
stack finished without qualification.

## Current Shipped Base

As of `2026-03-27`, the stack already has:

- native Groth16 / BN254 verifier support in the runtime
- registry-backed `vk_id` verification through `zk_registry`
- a note-based shielded fungible-token contract in `xian-contracts`
- Merkle-path-based `v2` circuits with a depth-20 append frontier
- wallet-side proving helpers in `xian-zk`
- separated spend keys and viewing keys
- encrypted on-chain payload delivery for note recovery
- optional disclosed viewers per output payload
- wallet-side seed backup, state snapshots, record sync, note selection, and
  request planning
- browser and mobile wallet flows for storing shielded `state_snapshot`
  backups, exporting them directly, and including them in full encrypted wallet
  backups
- exact withdraw support with zero outputs when no change note is required
- operator tooling to generate a random trusted-setup bundle and a
  registry-ready verifying-key manifest
- a first protocol-shaped shielded light-wallet history feed in `xian-abci`
  plus typed `xian-py` helpers and `xian-zk` wallet integration
- a standardized `xian-stack` operator path for BDS snapshot export/import

That is a serious candidate stack. It is not yet the final production shape.

## Still Missing

### 1. Ceremony-grade proving material flow

Current state:

- `xian-zk` can generate a single-party random setup bundle
- this is materially better than the deterministic dev bundle
- it is still not a multi-party ceremony

Still needed:

- import path for externally generated ceremony artifacts
- artifact validation and metadata checks before bundle acceptance
- operator documentation for ceremony provenance, custody, and rotation
- clear policy for which proving material is allowed on which network

Why it matters:

- this is the biggest remaining trust reduction gap in the proving stack

### 2. Network-level viewing and disclosure policy

Current state:

- output payloads can disclose to optional viewers
- wallets can recover disclosed payloads without spend authority

Still needed:

- network policy for when disclosure is expected, prohibited, or mandatory
- explicit roles such as issuer, auditor, regulator, or user-controlled viewer
- policy documentation for how disclosed viewing access is requested and audited
- guidance for contracts or apps that want selective disclosure without
  violating the privacy model

Why it matters:

- the cryptographic mechanism exists, but the product and governance rules do
  not

### 3. End-user wallet product layer

Current state:

- `xian-zk` now has a real Python wallet abstraction
- it supports note sync, planning, and recovery
- browser and mobile wallets now expose shielded snapshot backup/import/export
  flows directly in the product UI

Still needed:

- polished GUI / mobile / browser wallet UX
- recovery flows that are understandable to non-operators
- better user-facing note history and spend-status presentation
- transaction assembly flow that hides witness-management details from users
- eventually, a decision on whether the long-term public SDK surface should
  stay in `xian-zk` or move behind a higher-level SDK integration

Why it matters:

- today the stack is operator- and developer-usable, not mainstream-user-usable

### 4. Indexing and data-access hardening

Current state:

- the contract exposes root state, nullifier status, note count, and
  proof-bound payload hashes
- wallets now recover note payloads from indexed transaction history via BDS or
  another equivalent indexer feed
- the current branches now expose a first protocol-shaped
  `shielded_wallet_history` feed in `xian-abci` and `xian-py`
- `xian-stack` now standardizes BDS snapshot export/import as part of the
  operator recovery path

Still needed:

- better indexer / BDS exposure for shielded token metadata and note history
- pagination and watcher guidance for large live pools
- operational guidance for archive / retention expectations around encrypted
  payload blobs
- durable network-level compatibility commitments for the
  `shielded_wallet_history` feed and related wallet sync surfaces

Why it matters:

- indexed transaction recovery is the right architecture, but it still needs a
  more polished and more explicitly versioned app-facing read surface

### 5. Threat model and privacy-review pass

Current state:

- the implementation has tests and correctness hardening
- docs now explain privacy guarantees and non-guarantees
- a first explicit review now exists in `PRIVACY_ASSET_THREAT_MODEL.md`

Still needed:

- address the concrete findings from `PRIVACY_ASSET_THREAT_MODEL.md`
- operator policy for proving-bundle custody, provenance, and key-loss
  consequences
- public language for privacy expectations that avoids overclaiming
- network and product policy work for disclosure, metadata leakage, and
  retention-sensitive recovery paths

Why it matters:

- a privacy product is not complete when it only works cryptographically; the
  threat model has to be explicit

### 6. Canonical network packaging

Current state:

- operators can generate a bundle and manifest locally

Still needed:

- network-level packaging of approved verifying keys and contract presets
- a clear home for approved privacy-token deployment artifacts in network
  configuration repos
- release workflow for rotating or superseding proving material when needed

Why it matters:

- local artifact generation exists, but canonical network rollout policy does
  not

## Suggested Order

If work resumes later, the best order is:

1. external ceremony artifact import and verification
2. canonical network packaging and rollout policy
3. address the findings from `PRIVACY_ASSET_THREAT_MODEL.md`
4. network-level viewing / disclosure policy
5. end-user wallet product layer
6. richer indexer / BDS integration

## Boundary

This note is intentionally about the cross-repo product gap only.

Repo-local implementation details should stay in:

- `xian-contracting` for prover, wallet, and bundle-tooling internals
- `xian-contracts` for contract-specific changes
- `xian-docs-web` for public operator and developer guides
