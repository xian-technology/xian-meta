# Shared Foundations Plan

## Goal

Clean up the low-level shared Python code in the Xian workspace so that:

- `xian-abci` does not depend on `xian-py`
- shared foundations live in neutral ownership
- deterministic runtime types stay narrow and well-defined
- SDK convenience code stays in the SDK

## Current Problem

`xian-abci` currently depends on `xian-py` for two unrelated things:

- `Wallet`
- `ContractDecompiler`

That is the wrong dependency direction.

The node runtime should not depend on the external application SDK.

## Current Shared Foundation

`xian-runtime-types` already exists as a shared Python package. It currently
contains:

- deterministic decimal behavior
- deterministic encoding and decoding
- deterministic contract time types

This is a good shared foundation.

It is already used across the stack, but it lives inside the
`xian-contracting` repo today.

## Recommendation

### 1. Keep `xian-runtime-types` Narrow

Do not turn `xian-runtime-types` into a grab bag for all shared Python code.

It should stay focused on:

- deterministic value types
- deterministic encoding
- contract-time semantics

Do **not** add these to `xian-runtime-types`:

- wallets
- signing helpers
- key derivation
- contract decompilation
- SDK convenience helpers

Reason:

- those concerns are not “runtime types”
- they would pull unrelated dependencies into the most neutral shared layer
- they would blur deterministic-value semantics with crypto and tooling

### 2. `ContractDecompiler` Should Leave `xian-py`

The decompiler is not SDK-specific.

It is used for:

- readable contract display in the dashboard
- readable contract metadata persistence in BDS

It belongs closer to contract tooling.

Recommended home:

- `xian-contracting`

Preferred shape:

- move it into a clearly non-consensus-sensitive tool module such as
  `contracting.tools.decompiler`

### 3. Signing And Key Helpers Need Their Own Neutral Home

The key/signing functionality used by `Wallet` is shared infrastructure, not
SDK-only behavior.

It should move to a small neutral package with a narrow API.

Preferred package:

- `xian-accounts`

Initial scope:

- derive Ed25519 public key from private key
- sign message
- verify message
- normalize key formats used across the stack

Keep the richer user-facing `Wallet` class in `xian-py`, but make it a wrapper
over that shared foundation.

## Repo Strategy

### Short-Term Recommendation

Do **not** block the current cleanup on a repo extraction.

First fix the package and dependency boundaries:

1. move `ContractDecompiler` into `xian-contracting`
2. introduce `xian-accounts` as a neutral shared package
3. update `xian-py.Wallet` to use `xian-accounts`
4. update `xian-abci` to depend on `xian-accounts` and contract tooling, not on
   `xian-py`

### Long-Term Recommendation

Yes, `xian-runtime-types` is a strong candidate for leaving the
`xian-contracting` repo and becoming a separately owned shared foundation.

That makes sense because it is:

- small
- stable
- neutral
- already used across multiple major repos

But that should be treated as a second cleanup, not as the prerequisite for the
current dependency fix.

## Why Not Put Everything In One Shared Package?

Because the shared layer should stay easy to understand.

These are different categories:

- deterministic runtime values: `xian-runtime-types`
- account/signing primitives: `xian-accounts`
- contract source tooling: `xian-contracting`

Merging them into one package would make the low-level boundary less clear, not
more clear.

## Proposed End State

- `xian-runtime-types`
  - deterministic decimals, encoding, time
- `xian-accounts`
  - signing, verification, public-key derivation, account helpers
- `xian-contracting`
  - runtime, compiler, decompiler, contract tooling
- `xian-py`
  - SDK clients, app-facing wallet UX, transport, watcher, projector helpers
- `xian-abci`
  - node runtime with no dependency on the SDK

## Migration Order

1. move `ContractDecompiler` out of `xian-py`
2. create `xian-accounts`
3. switch `xian-py.Wallet` to it
4. switch `xian-abci` genesis/state-export code to it
5. remove `xian-py` from `xian-abci` runtime dependencies
6. after that, decide whether to extract `xian-runtime-types` into its own repo

## Decision

Extracting `xian-runtime-types` into its own repo makes sense.

Adding signing/key helpers to `xian-runtime-types` does not.

The immediate cleanup should focus on dependency direction and package
responsibility first. Repo extraction can follow once those boundaries are
clean.

## Progress

Completed:

- `ContractDecompiler` moved into the `xian-contracting` repo as the standalone
  `xian-contract-tools` package
- `xian-abci` BDS and dashboard paths now import decompiler tooling from
  `xian-contract-tools` instead of `xian-py`
- `xian-py` now depends on `xian-contract-tools` for clean contract rendering
  instead of owning the implementation itself
- release metadata and trusted publisher docs were updated for
  `xian-contract-tools`

Next:

- create `xian-accounts`
- migrate `Wallet` internals to it
- remove the remaining `xian-abci -> xian-py` dependency
