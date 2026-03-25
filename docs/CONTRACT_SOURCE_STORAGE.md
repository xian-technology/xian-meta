# Contract Source Storage

## Goal

Make contract source retrieval exact and cheap for newly submitted contracts.

The main requirement is:

- the stack must be able to return the original submitted contract source
  directly

That is different from the current best-effort decompiler flow, which only
works from transformed stored code.

## Current State

Today `xian-contracting` stores:

- `contract.__code__`: canonical transformed source produced by the compiler
- `contract.__compiled__`: marshaled Python bytecode for runtime loading

The original submitted source is not stored.

That means the original source is already lost before:

- `xian-abci` dashboard reads it
- BDS indexes it
- `xian-py` tries to render it cleanly

The current `ContractDecompiler` is therefore not a true decompiler. It is a
best-effort source restorer for canonical transformed code.

## Problem

Even a good decompiler cannot recover the original authored contract exactly
from `__code__` alone.

What is already lost today:

- comments
- blank-line structure
- exact quote style
- some author naming intent after compiler transforms
- any formatting detail not preserved by AST round-tripping

So if the requirement is “show me the contract as it was submitted”, improving
the decompiler is not enough.

## Decision

For newly submitted contracts, store both:

- `contract.__source__`: exact submitted source
- `contract.__code__`: canonical transformed source used by the runtime
- `contract.__compiled__`: compiled runtime artifact

Optional metadata that may also be worth storing:

- `contract.__source_hash__`
- `contract.__compiler_version__`
- `contract.__source_format__`

The authoritative source of truth should be consensus state, not BDS.

## Storage Location

The original source should be stored in the same authoritative contract state
store as the rest of contract metadata.

That means:

- it lives in LMDB through the normal `Driver` contract metadata path
- it is part of exported/imported state snapshots
- it is available even when BDS is disabled

BDS may index or cache it, but BDS should not be the only place where it
exists.

## Why Not Store It Only In BDS?

Because BDS is optional.

If the original contract source matters as part of the contract record, it
belongs in the canonical state layer.

Otherwise:

- source retrieval depends on an optional service
- snapshot/export/import does not preserve the full authored contract record
- explorers and SDKs do not have one authoritative source of truth

## Recommended Retrieval Order

For user-facing source display:

1. `__source__` if present
2. `decompile(__code__)` if `__source__` is absent
3. raw `__code__` as the last fallback

That gives:

- exact authored source for new contracts
- readable fallback for older contracts
- deterministic escape hatch when decompilation fails

## BDS Role

BDS still has value even if source is stored in canonical state.

Recommended BDS behavior:

- index contract submission metadata
- cache the preferred display source
- optionally keep both source forms if useful for tooling

Minimum good shape:

- `contracts.code` becomes the preferred display source
- prefer `__source__`
- fall back to decompiled `__code__`

If deeper tooling becomes important later, BDS can grow explicit columns for:

- `source`
- `canonical_code`
- `source_kind`

That is not required for the initial improvement.

## API Shape

If the stack were defined fresh, the clean contract-query shape would be:

- `contract_source/<name>`: exact submitted source if available
- `contract_code/<name>`: canonical transformed source
- `contract/<name>`: preferred human-readable source

That keeps the concepts separate:

- authored source
- runtime source
- display source

The current single `/contract/<name>` path conflates those concepts.

## Decompiler Value After Source Storage

The decompiler still has value, but its role changes.

It remains useful for:

- legacy contracts that only have `__code__`
- fallback rendering when `__source__` is missing
- tooling that wants normalized readable code from canonical runtime source
- debugging compiler transforms

It should no longer be treated as the main path for contract display when
`__source__` exists.

## Comparison With Other Chains

The common pattern across major smart-contract platforms is:

- store the executable artifact on-chain
- keep source separate
- use verification or metadata to connect the two

Xian can choose a friendlier model because its contract source is already a
first-class part of the development experience.

Storing both `__source__` and `__code__` in canonical state is a reasonable
product choice, even if it is more source-heavy than most chains.

## Recommended Implementation Order

1. add `SOURCE_KEY = "__source__"` to contract storage
2. store original source in `Contract.submit(...)`
3. export/import `__source__` through state snapshot and genesis flows
4. update `xian-abci` query/dashboard paths to prefer `__source__`
5. update BDS contract ingestion to prefer `__source__`
6. update `xian-py` contract reads to prefer `__source__`
7. keep decompiler as a fallback only

## Decision

Recommended stance:

- keep the decompiler
- stop depending on it for exact source retrieval
- store original source directly in canonical state

That is the cleanest way to get exact contract source while preserving readable
fallback behavior for existing contracts.
