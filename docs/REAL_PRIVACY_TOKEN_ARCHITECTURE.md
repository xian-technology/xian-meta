# Real Privacy Token Architecture

Status: proposed

This document defines the path for turning Xian's current experimental
privacy-token work into a real shielded token design.

## Decision

Xian should not try to harden the current
`contracts/privacy-token/src/con_privacy_token.py` into a production privacy
primitive.

Instead, Xian should build a new shielded-token model based on:

- shielded notes
- nullifiers
- Merkle-root state
- native zero-knowledge proof verification in the runtime

The current commitment-only contract remains a research artifact. It is not the
production base.

## Why The Current Contract Cannot Become The Real Thing

The current experimental contract proves only algebraic consistency between
stored commitments. It does not prove:

- that a transfer amount corresponds to a meaningful hidden value
- that a burn amount corresponds to a meaningful hidden value
- that a note owner knows the note secret
- that a note exists in a committed state tree
- that a note has not already been spent
- that hidden amounts are non-negative and conserved

This was confirmed locally on `2026-03-26`:

- a holder can mint with one public amount and later burn with a completely
  different public amount while still satisfying the contract's current
  invariant checks
- zero commitments are accepted and can collapse the supply commitment into a
  degenerate state

Those are not patch-level issues. They are consequences of the model.

## Current Runtime Limitation

Today Xian contracts expose:

- hashing helpers like `sha3` / `sha256`
- Ed25519 signature verification

They do not expose:

- a SNARK verifier
- a proof-friendly Merkle primitive
- circuit-verified nullifier handling
- a native shielded-note execution surface

That means a real privacy token is not a contract-only feature. It requires new
runtime support.

## Product Goal

The target is a shielded fungible token where:

- balances are represented as private notes, not public account balances
- spends are authorized by zero-knowledge proof, not by revealing balances
- double-spends are prevented through nullifiers
- note existence is proven against an accepted Merkle root
- hidden value conservation is enforced by the circuit
- public mint and burn operations remain possible when desired

This is a real privacy-token model. It is not equivalent to "opaque
commitments on public accounts."

## Recommended Architecture

### Model

Use a note-based UTXO model, not an account-balance model.

Each note should commit to at least:

- asset identifier
- amount
- owner key
- blinding / randomness
- note salt

Each spend produces:

- one or more nullifiers for consumed input notes
- one or more new output note commitments
- a proof that the transition is valid

### Why Notes Instead Of Account Commitments

Note-based shielded systems solve the real hard problems cleanly:

- ownership is proven in circuit
- double-spends are blocked by nullifiers
- state membership is proven by Merkle path
- hidden values are range-checked and conserved in circuit

The current account-commitment model has no clean way to achieve those
properties without effectively turning into a note system anyway.

## Required Runtime Primitive

### Minimal required primitive

Add a native proof verification bridge to the contract runtime:

- `zk.verify_groth16(vk_id, proof, public_inputs) -> bool`

The contract should not implement proof verification in Python.

### Why this is the minimum

If the proof circuit enforces:

- note membership under `old_root`
- nullifier correctness
- output commitment correctness
- hidden amount conservation
- authorized spend
- Merkle-root transition from `old_root` to `new_root`

then the on-chain contract does not need to implement those cryptographic
checks itself. It only needs to:

- verify the proof
- reject reused nullifiers
- advance the accepted root set
- append or record emitted commitments

This keeps the contract small and deterministic.

### Preferred proving stack

For the first real implementation, use a Groth16-style proof system with a
stable native verifier.

The main reason is practicality:

- compact proofs
- fast on-chain verification
- mature circuit tooling

The exact proving backend can still be chosen later, but the runtime interface
should be proof-system specific and explicit, not generic hand-waving.

## Contract State Model

The production privacy-token contract should store:

- current accepted Merkle root
- recent root history for delayed witness usage
- spent nullifiers set
- emitted note commitments
- public supply, if the chosen design exposes public mint / burn
- operator / admin configuration

It should not store "private balances per address."

## Canonical Operations

### 1. Deposit / Mint

Public input:

- recipient shielded note commitment(s)
- public amount
- proof
- old root
- new root

Effect:

- public reserve / supply increases
- new shielded notes are created
- new root becomes accepted

### 2. Shielded Transfer

Public input:

- old root
- new root
- input nullifiers
- output commitments
- proof

Effect:

- input notes become unspendable through nullifier marking
- output notes are created
- no public amount is revealed

### 3. Withdraw / Burn

Public input:

- old root
- new root
- input nullifiers
- optional change note commitments
- public recipient
- public amount
- proof

Effect:

- shielded value is destroyed inside the note set
- public token amount is released to a visible address

## Security Requirements

The real implementation must enforce all of these at proof level:

- note ownership
- note existence under an accepted root
- nullifier correctness
- nullifier uniqueness
- hidden amount conservation
- non-negative bounded amounts
- asset identity binding

The contract must enforce:

- nullifier non-reuse
- accepted root membership / rollover policy
- admin permission checks
- deterministic proof-verifier invocation
- replay safety for public actions

## What Should Stay Public

The first real version should keep these public:

- contract-level configuration
- nullifiers
- note commitments
- Merkle roots
- deposit and withdrawal events

That still gives meaningful privacy:

- hidden amounts
- hidden ownership of output notes
- unlinkability between shielded inputs and outputs except through public
  operational patterns

## What Should Not Be In V1

Do not try to add all of this to v1:

- private smart-contract calls
- general shielded multi-contract composability
- private AMM state
- viewing-key recovery logic
- multiple proving systems
- generalized anonymous account model

V1 should be:

- one shielded fungible-token system
- one proof backend
- one clearly documented note model

## Repo Changes Required

### `xian-contracting`

Add:

- native `zk` verification bridge
- deterministic verifier wiring
- explicit gas / stamp pricing for proof verification
- tests with fixed proof vectors

### `xian-abci`

Add:

- execution metering and validation for the verifier bridge
- metrics around proof verification cost / failures
- compatibility validation in repo tests

### `xian-py`

Add:

- note wallet model
- witness management
- proof-generation integration surface
- deposit / transfer / withdraw builders

### `xian-contracts`

Add:

- a new privacy-token package, not an in-place mutation of the current one
- package-local contract tests
- fixed proof-vector tests
- docs and operator guidance

### `xian-docs-web`

Add:

- shielded-token model docs
- wallet / witness lifecycle docs
- clear privacy guarantees and non-guarantees

## Recommended Phases

### Phase 1: Runtime groundwork

- choose the proving backend
- implement native proof verification
- define proof verification metering
- build deterministic verifier tests

### Phase 2: Minimal shielded token

- one asset
- deposit
- shielded transfer
- withdraw
- fixed proof vectors
- no viewing-key features

### Phase 3: Wallet and indexing

- witness sync
- note scanning
- nullifier tracking
- SDK transaction builders

### Phase 4: Product hardening

- performance review
- operator documentation
- threat model review
- privacy caveat documentation

## Explicit Non-goal

The current `con_privacy_token.py` should not be "incrementally fixed" until
it magically becomes production-grade privacy. That would produce a misleading
contract with stronger marketing than guarantees.

The correct path is a new implementation built on real proof verification.

## Immediate Next Step

The next concrete step is not editing the current contract.

The next step is to write the runtime verifier design for `xian-contracting`,
including:

- the exact verifier interface
- proof encoding
- verification-key registration model
- metering
- deterministic test-vector strategy
