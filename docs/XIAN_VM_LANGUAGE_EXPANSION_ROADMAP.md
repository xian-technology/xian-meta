# Xian VM Language Expansion Roadmap

Xian defines the contract language through its native V2 compiler and VM.
The [supported syntax](https://docs.xian.technology/smart-contracts/valid-code)
and [value methods](https://docs.xian.technology/smart-contracts/value-methods)
are documented for contract authors. The current runtime boundary is recorded in
[Compiler Runtime Launch Status](COMPILER_RUNTIME_LAUNCH_STATUS.md).

## Decision Rule

Add a language feature when its semantics are deterministic across nodes,
its boundary values have canonical representations, and its work is bounded
and meterable. Make host interactions explicit and justify the permanent
protocol surface with an authored contract use case.

## Implemented Surface

The VM already supports the string, list, and dictionary methods identified
in the initial ergonomics work, including `split`, `strip`, `upper`,
`endswith`, `find`, list `index`, `count`, `clear`, and `copy`, and
dictionary `pop`. Both `for` and `while` support an `else` suite.
The runtime supports `bytes`, `bytearray`, `set()`, and `frozenset()`.
`map()` and `filter()` produce eager lists.

## Open Work

### Deterministic ergonomics

Use authored contracts and conformance gaps to select any additional helpers
or edge cases. The existing test surfaces track supported features and
explicit exclusions.

### Set syntax

The compiler rejects set literals and set comprehensions. Decide whether to add
either syntax, and define its evaluation order, duplicate handling, and work
limits if accepted. The VM already has deterministic set values.

### Callable and iterator semantics

Consider additional callable values or lazy iterators when a contract use case
justifies them. Specify how callable values are represented, what can cross a
VM boundary, and how deferred work is bounded and metered. Preserve the eager
behavior of `map()` and `filter()` unless a versioned change explicitly revises it.

### Excluded capabilities

Keep `eval`, `exec`, arbitrary reflection, ambient state mutation, arbitrary
filesystem/network/process access, and imports outside the explicit contract
import surface out of the language.

## Evidence For A Language Change

Record the semantics and update the
[runtime surface cases](../../xian-contracting/tests/surface/README.md).
Add authored-contract or replay-derived cases where the change affects those
paths. Use the
[native determinism campaign](../../xian-contracting/tests/determinism/README.md)
for compiler and runtime observations. Historical Python and V1 results are
available as compatibility evidence for the semantics they observed.
