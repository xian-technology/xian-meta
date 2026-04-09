# Privacy Asset Threat Model

Status: first review on 2026-04-09

This note is the first explicit threat-model and privacy-review pass for the
current Xian shielded asset stack after the `zk-runtime-optimization` work in:

- `xian-contracting`
- `xian-contracts`
- `xian-abci`
- `xian-py`

It is intentionally blunt. The goal is to state what the stack does and does
not protect, where the real trust boundaries still are, and what follow-up work
still has to happen before the system can be described as a finished privacy
product.

## Executive Summary

The stack is now a real proof-backed shielded asset candidate. The main
remaining risks are not "does the proof arithmetic exist?" but:

1. proving-material trust
2. prover-service trust
3. network-origin privacy
4. indexed recovery and retention policy
5. disclosure policy and operator rules

That means the stack is strong enough to describe as a candidate shielded asset
system with explicit caveats. It is not yet accurate to market it as:

- ceremony-grade trust-reduced
- network-anonymous
- policy-complete
- consumer-wallet-complete

## What The Stack Tries To Protect

Against a normal on-chain observer, the design aims to hide:

- shielded note amounts inside the private pool
- note ownership
- which prior note funded which later note
- note plaintext inside encrypted payload blobs

For newer payloads, the stack also avoids embedding recipient viewing public
keys in cleartext. Wallet sync can prefilter candidates through anonymous
discovery metadata rather than broad plaintext scanning.

## What The Stack Does Not Try To Protect

The current design does not fully hide:

- transaction submission timing
- network origin or first-hop source
- target contract activity and public side effects
- public mint / withdraw effects
- proving-material provenance risk
- witness exposure to the prover service
- anything deliberately disclosed to extra viewers

The design also depends on indexed transaction history for practical wallet
recovery. That is an acceptable architecture choice, but it creates operational
and retention requirements.

## System Boundary

This review covers:

- `shielded-note-token`
- `shielded-commands` and relayed shielded transfers
- `xian-zk` wallet, prover, bundle, and prover-service tooling
- `zk_registry`
- the BDS / indexed-query recovery path
- browser / mobile wallet integration expectations

It does not attempt a formal cryptographic proof review of Groth16, BN254, or
the underlying circuit soundness. It assumes the implemented verifier and
circuits are functionally correct unless a separate cryptographic audit says
otherwise.

## Findings

### 1. High: proving material is still trusted single-party setup

Current state:

- `xian-zk` can generate a random deployment bundle and registry manifest
- that is materially better than the deterministic dev bundle
- it is still explicitly not an MPC ceremony

Risk:

- whoever generates the proving material may retain toxic waste
- malicious or substituted artifacts can undermine the privacy system before
  deployment
- operators do not yet have a canonical custody / provenance / rotation policy

Implication:

- the system currently relies on trusted proving-material generation and trusted
  bundle custody

Required follow-up:

- import path for externally generated ceremony artifacts
- artifact validation before acceptance
- network policy for approved proving material
- operator runbook for custody, backup, and rotation

### 2. High: the prover service is trusted and sees witness material

Current state:

- the prover service binds to `127.0.0.1` by default
- it supports bearer-token authentication
- the implementation and docs explicitly warn that witness material is exposed
  to the service

Risk:

- local malware or host compromise can read witness material
- remote deployment or unsafe host binding would expand the trust boundary in a
  dangerous way
- users may misread "prover offload" as "split-prover privacy" when that is not
  true

Implication:

- the prover service is a usability / deployability improvement, not a witness
  privacy guarantee

Required follow-up:

- keep the local-only default and explicit warnings
- do not market the service as equivalent to split proving
- design a true split-prover protocol if witness-exposure reduction is required

### 3. High: network-origin privacy is still incomplete

Current state:

- on-chain sender privacy is stronger than network-origin privacy
- the current design still assumes a normal transaction submission path
- the docs already acknowledge that hidden on-chain sender is incomplete if the
  first peer can still identify the source

Risk:

- an observer near the transaction origin can correlate a supposedly private
  action to the submitting wallet or relayer
- on-chain shielding does not stop mempool / ingress metadata correlation

Implication:

- the current stack is shielded on-chain, not network-anonymous

Required follow-up:

- private submission layer such as relayer-mesh or Dandelion++ style propagation
- explicit user-facing language that separates on-chain privacy from network
  privacy

### 4. Medium: wallet recovery depends on indexed history and retention policy

Current state:

- wallet recovery now uses indexed transaction history instead of reading
  payloads from contract state
- the `zk-runtime-optimization` branches add a first selective output-tag query
  path in `xian-abci` and `xian-py`
- encrypted payload blobs and discovery metadata therefore matter operationally
  outside consensus state

Risk:

- insufficient retention or incomplete reindex capability can break historical
  note recovery
- operational teams may prune or archive data in ways that are acceptable for a
  public token but harmful for shielded wallet recovery
- indexers can observe encrypted payload blobs and discovery-tag traffic even
  though they cannot read note plaintext

Implication:

- privacy and recoverability now depend partly on indexer operations, not only
  on-chain contract state

Required follow-up:

- retention / archival guidance for encrypted payload history
- stable wallet-facing query helpers for note history and metadata
- operator guidance for reindex and recovery against archival sources

### 5. Medium: disclosure mechanics exist without a network-level policy

Current state:

- the payload format supports optional disclosed viewers
- wallets can recover disclosed payloads without spend authority
- there is still no network policy for when disclosure is expected, forbidden,
  or mandatory

Risk:

- applications can make inconsistent disclosure choices
- users may overestimate default privacy if disclosure is product-driven but not
  clearly explained
- issuer / auditor / regulator expectations can diverge across deployments

Implication:

- the mechanism exists, but the governance and product semantics are incomplete

Required follow-up:

- policy for issuer, auditor, regulator, and user-controlled viewer roles
- explicit guidance for selective-disclosure UX and auditability

### 6. Medium: public side effects and timing still allow correlation

Current state:

- target calls and public side effects remain visible on-chain
- public withdraws, public adapter effects, relayer fees, and event timing can
  still be correlated externally
- recent-root proving helps usability, but it does not remove timing metadata

Risk:

- repeated use patterns can leak behavior even when note ownership and note
  values remain hidden
- observers can correlate shielded actions with nearby public effects

Implication:

- shielding reduces value / ownership visibility, but not all behavioral
  observability

Required follow-up:

- conservative public-facing claims about what "private" means here
- wallet UX that explains which outputs and side effects stay public

### 7. Medium: root-history and sync behavior are a privacy-liveness tradeoff

Current state:

- the design keeps recent root history for delayed witness usage
- wallets can prove against a recent accepted root rather than only the latest
  root
- the recent-root window is still bounded

Risk:

- stale wallets can fail in ways users misread as privacy or correctness bugs
- forced resync behavior can reveal wallet recency and create operator support
  burden

Implication:

- root-history design helps usability, but it still needs operator and wallet
  guidance

Required follow-up:

- explicit wallet messaging around stale witnesses and resync
- operator guidance for root-history changes and recovery expectations

## What The Review Says Today

Accurate claims:

- Xian has a proof-backed shielded asset stack candidate
- note ownership and note values are meaningfully protected on-chain
- the stack supports viewing-key-based recovery and optional disclosure
- the runtime and indexing branches materially improve cost and wallet sync

Inaccurate claims:

- "the stack has ceremony-grade trust reduction"
- "the prover service preserves witness privacy"
- "shielded transfers are network-anonymous"
- "the privacy model is complete and policy-settled"

## Immediate Actions

1. Land ceremony-artifact import and validation.
2. Write operator policy for bundle custody, provenance, and rotation.
3. Keep the prover service explicitly local and trusted-only.
4. Write the network-level disclosure policy.
5. Finish the retention / archival guidance for indexed encrypted payloads.
6. Keep wallet messaging conservative about what is and is not hidden.
