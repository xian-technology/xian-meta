# ZK Verifier Runtime

Status: proposed

This document defines the first runtime verifier surface required for a real
privacy token in Xian.

It is the immediate follow-up to:

- `REAL_PRIVACY_TOKEN_ARCHITECTURE.md`

## Decision

Xian should add a native zero-knowledge proof verification bridge to the
contract runtime.

The first supported proof family should be:

- Groth16
- BN254

The verifier should be implemented as a native Rust-backed package exposed to
the Python runtime, not as a pure-Python cryptography package.

## Why Not A Pure Python Package

The validator-facing verifier is consensus-critical code. The priority order
is:

- deterministic behavior
- correctness
- auditability
- performance
- maintainable packaging

Pure Python zk libraries are not the right base for that verifier layer.

Reasons:

- pairing-heavy verification in pure Python is too slow for validator hot paths
- many Python zk packages are proving-oriented or research-oriented, not narrow
  production verifier packages
- Python-level bigint and serialization behavior is easier to misuse
- we want a small, explicit runtime surface, not a general cryptography
  playground inside contracts

Python packages can still be useful for:

- developer experiments
- reference implementations
- wallet-side tooling

They should not be the primary validator verifier.

## Package Evaluation

### `py_ecc`

Useful as:

- reference ECC / pairing implementation
- tests and cross-checking

Not recommended as the production runtime verifier because:

- it is pure Python
- it is lower-level than the interface we want
- it does not give us a narrow production verifier surface out of the box

Reference:

- https://github.com/ethereum/py_ecc

### `PySNARK`

Useful as:

- a research/prototyping system

Not recommended as the runtime verifier because:

- it is oriented around proving workflows and experiments
- it does not match the narrow validator-verifier role we need

Reference:

- https://github.com/Charterhouse/pysnark

### `gnark`

Strong project, but not the preferred runtime verifier base for Xian because:

- it is Go-based
- direct embedding into the current Python contract runtime is awkward
- it adds another runtime-language boundary on the verifier hot path

It may still be useful later as an off-chain proving stack.

Reference:

- https://github.com/ConsenSys/gnark

### `arkworks` / `ark-groth16`

This is the preferred base.

Why:

- mature Rust ecosystem for zk primitives
- explicit Groth16 verification support
- good fit for a small native verifier package exposed to Python
- easier to package with PyO3/maturin than a Go verifier path

Reference:

- https://docs.rs/ark-groth16/latest/ark_groth16/

## Recommended Implementation Shape

Build a small native package, conceptually:

- `xian-zk`

It can live inside `xian-contracting` at first, the same way `xian-accounts`
and `xian-contract-tools` do today.

Responsibilities:

- proof decoding
- verifying-key decoding
- verifier invocation
- deterministic error handling
- no proving logic

It should not become a general-purpose zk toolkit.

## Runtime Surface

Expose one narrow bridge into contracts:

- `zk.verify_groth16(vk_id: str, proof: str, public_inputs: list[str]) -> bool`

Definitions:

- `vk_id`: identifier for a registered verifying key
- `proof`: canonical encoded proof bytes as hex
- `public_inputs`: canonical encoded field elements as hex strings

This should be read-only and side-effect free.

## Why `vk_id` Instead Of Passing The Full Verifying Key

Passing the verifying key in every contract call is the wrong model because:

- it is large
- it is repetitive
- it complicates metering
- it weakens cacheability

Instead:

- verifying keys are registered once
- proofs reference them by stable id
- the runtime fetches and caches the decoded/prepared key

## Verifying Key Registry

The verifying-key registry must be deterministic across validators.

The cleanest v1 model is:

- a system contract stores verifying-key records in canonical state
- the runtime bridge loads by `vk_id`
- the native verifier caches decoded prepared keys locally by
  `(vk_id, vk_hash)`

Minimal stored registry fields:

- `scheme`: `"groth16"`
- `curve`: `"bn254"`
- `vk_bytes`
- `vk_hash`
- `created_at`
- `active`

Optional metadata:

- `circuit_name`
- `version`
- `owner`

## Encoding Rules

Do not use ad hoc Python dicts or floats for proof verification inputs.

### Public inputs

Use:

- `0x`-prefixed 32-byte big-endian field-element hex strings

This keeps the contract API deterministic and easy to validate.

### Proofs

Use:

- canonical `0x`-prefixed hex encoding of the proof bytes in the chosen
  verifier format

The native verifier package is responsible for decoding this into the Rust-side
proof structure.

### Verifying keys

Store:

- canonical serialized bytes
- deterministic hash

The exact serialization format should be fixed by the native package and
documented alongside it.

## Metering

Proof verification must have explicit stamp pricing.

The first design should charge:

- fixed base cost for verifier invocation
- per-public-input incremental cost
- additional one-time decode cost when a verifying key is first loaded locally

The cached-key fast path and cold-key path should be different internally, but
the contract-facing metering should remain deterministic and conservative.

## Cache Model

The runtime should cache prepared verifying keys in-process.

Recommended cache key:

- `(vk_id, vk_hash)`

Recommended implementation:

- small in-process LRU cache in Python runtime state
- native verifier package owns parsed/prepared VK structures

If the hash changes, the old entry is invalid.

## Error Model

The bridge must not leak backend-specific chaos into contracts.

Contract-visible behavior should be:

- return `True` for valid proof
- return `False` for invalid proof
- raise only for malformed usage:
  - unsupported scheme
  - unknown `vk_id`
  - malformed hex / malformed public-input format

This keeps contract logic predictable.

## First Privacy-Token Dependency

The first real shielded token should rely on this verifier bridge to prove:

- membership under an accepted Merkle root
- nullifier correctness
- output commitment correctness
- hidden amount conservation
- note ownership

Without this bridge, that token should not be implemented as a production
feature.

## Security Constraints

The runtime bridge must:

- pin crate versions tightly
- avoid optional algorithm auto-selection
- avoid network access or external proving services
- use deterministic decoding and field checks
- reject malformed points and malformed field elements explicitly

The contract layer must:

- treat `vk_id` as policy-controlled
- maintain nullifier state
- maintain accepted root state
- not re-implement proof verification logic in Python

## Non-goals

Do not include these in v1:

- proof generation inside validators
- generic proving APIs inside `xian-py`
- multiple proof systems
- recursive verification
- universal zk VM support
- custom curves per contract

V1 should be one narrow verifier path.

## Recommended Package Choice

The best current direction is:

- Rust native package
- `ark-groth16`
- BN254 first
- Python binding via PyO3/maturin

This gives Xian:

- a serious verifier path
- a small Python integration surface
- a package story that still fits the rest of the stack

## Suggested Contract API Surface

Inside contracts:

- `zk.verify_groth16(vk_id, proof, public_inputs)`

Optional helper APIs later:

- `zk.hash_public_inputs(...)`
- `zk.supported_verifiers()`

Do not start with more than that.

## Suggested Implementation Phases

### Phase 1

- native Rust verifier package
- fixed proof vectors
- Python bridge
- no contract exposure yet

### Phase 2

- `zk.verify_groth16(...)` contract bridge
- verifying-key registry contract
- metering
- repo validation and benchmarks

### Phase 3

- first shielded-token contract
- SDK-side proof submission tooling
- docs and operator guidance

## Immediate Next Step

Implement the native verifier package prototype in `xian-contracting` and prove
that:

- a fixed verifying key can be loaded
- a fixed proof can be verified
- malformed proofs are rejected deterministically
- Python binding overhead is acceptable for validator execution
