# Contract Source Storage

## Goal

Make contract source retrieval direct, deterministic, and cheap for newly
submitted contracts.

The main requirement is:

- the stack must be able to return a clean human-readable contract source
  directly, without decompilation

For this design, “source” does not mean byte-for-byte original text. It means
the canonical user-facing source form of the contract.

## Current State

Today `xian-contracting` stores:

- `contract.__code__`: canonical transformed source produced by the compiler
- `contract.__compiled__`: marshaled Python bytecode for runtime loading

The submitted source is not stored.

That means the user-facing source is already lost before:

- `xian-abci` dashboard reads it
- BDS indexes it
- `xian-py` tries to render it cleanly

The current `ContractDecompiler` is therefore not a true decompiler. It is a
best-effort source restorer for canonical transformed code.

## Problem

Even a good decompiler cannot recover a clean, reliable author-facing contract
representation from `__code__` alone.

What is already lost today:

- comments
- blank-line structure
- exact quote style
- some author naming intent after compiler transforms
- any formatting detail not preserved by AST round-tripping

So if the requirement is “show me the contract source directly”, improving the
decompiler is the wrong solution.

## Decision

For newly submitted contracts, store both:

- `contract.__source__`: canonical user-facing source
- `contract.__code__`: canonical transformed runtime source

Do not persist `contract.__compiled__` in canonical state.

Instead:

- compile `__code__` locally as needed
- keep compiled code in a local process cache only

### Meaning Of `__source__`

`__source__` should not be raw submitted text.

It should be the submitted contract after:

- parsing to AST
- dropping comments implicitly
- normalizing formatting via `ast.unparse(...)`
- before compiler transforms like `@export -> @__export(...)`,
  `seed -> ____`, ORM keyword injection, private-name rewriting, and decimal
  lowering

That gives a clean source form with these properties:

- no decompiler needed for normal source display
- comments do not bloat state
- formatting is deterministic
- user-facing names and decorators are preserved

It intentionally does not preserve:

- comments
- blank-line style
- exact quoting style
- byte-for-byte source text

Optional metadata that may also be worth storing:

- `contract.__source_hash__`
- `contract.__compiler_version__`
- `contract.__code_hash__`

The authoritative source of truth should be consensus state, not BDS.

## Storage Location

The canonical source should be stored in the same authoritative contract state
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
- snapshot/export/import does not preserve the full contract record
- explorers and SDKs do not have one authoritative source of truth

## Recommended Retrieval Order

For user-facing source display:

1. `__source__` if present
2. raw `__code__` as the last fallback

That gives:

- clean canonical source for new contracts
- deterministic fallback for older contracts

## BDS Role

BDS still has value even if source is stored in canonical state.

Recommended BDS behavior:

- index contract submission metadata
- cache the preferred display source
- optionally keep both source forms if useful for tooling

Minimum good shape:

- `contracts.code` becomes the preferred display source
- prefer `__source__`
- fall back to raw `__code__`

If deeper tooling becomes important later, BDS can grow explicit columns for:

- `source`
- `canonical_code`
- `source_kind`

That is not required for the initial improvement.

## API Shape

If the stack were defined fresh, the clean contract-query shape would be:

- `contract_source/<name>`: canonical user-facing source if available
- `contract_code/<name>`: canonical transformed source
- `contract/<name>`: preferred display source

That keeps the concepts separate:

- user-facing source
- runtime source
- display source

The current single `/contract/<name>` path conflates those concepts.

## Decompiler Value After Source Storage

This design removes the need for the decompiler.

For newly submitted contracts:

- normal display uses `__source__`
- runtime uses `__code__`

For older contracts:

- the stack should return `__code__` directly as fallback unless a migration
  pass backfills `__source__`

So the preferred direction is:

- stop depending on decompilation entirely
- remove the decompiler package once the stack no longer uses it

## Comparison With Other Chains

The common pattern across major smart-contract platforms is:

- store the executable artifact on-chain
- keep source separate
- use verification, metadata, or source maps to connect the two

Xian can choose a friendlier model because its contract source is already a
first-class part of the development experience.

Storing both `__source__` and `__code__` in canonical state is a reasonable
product choice, even if it is more source-heavy than most chains.

### Storage And Metering Implication

Write metering in Xian is byte-based.

That means:

- if raw commented source were stored in state, comments would cost stamps

This is one of the main reasons `__source__` should be canonicalized without
comments before storage.

## Compiled Code Cache

`__compiled__` should become an in-process cache, not a canonical state key.

Recommended approach:

- compile from `__code__` on first load
- cache compiled code objects in-process using `cachetools`
- key the cache by `(contract_name, code_hash)`
- invalidate automatically when the code hash changes

Why this is the right cache shape:

- `cachetools` is already used in the stack
- it is established and fast
- no custom cache implementation is needed
- it keeps compiled artifacts local to the process that executes them

## Recommended Implementation Order

1. add `SOURCE_KEY = "__source__"` to contract storage
2. derive canonical `__source__` from the submitted AST before runtime transforms
3. keep storing canonical transformed `__code__`
4. stop storing `__compiled__` in state
5. add in-process compiled-code caching keyed by `(name, code_hash)`
6. export/import `__source__` through snapshot and genesis flows
7. update `xian-abci` query/dashboard paths to prefer `__source__`
8. update BDS contract ingestion to prefer `__source__`
9. update `xian-py` contract reads to prefer `__source__`
10. remove decompiler usage and eventually the package itself

## Decision

Recommended stance:

- store canonical user-facing source directly in canonical state
- keep canonical transformed runtime source directly in canonical state
- stop persisting compiled bytecode in canonical state
- remove the decompiler once the stack no longer needs it

That is the cleanest way to get direct contract source retrieval without
introducing decompilation heuristics or paying stamp costs for comments.
