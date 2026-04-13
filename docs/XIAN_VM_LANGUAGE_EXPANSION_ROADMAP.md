# Xian VM Language Expansion Roadmap

## Purpose

This document defines how the contract language should grow now that Xian owns
its execution VM instead of inheriting the old CPython execution boundary.

The goal is not "more Python because Python has it".

The goal is a larger, cleaner, intentionally designed Xian contract language
with explicit VM semantics.

## Decision Rule

A new language feature should be added only if it is:

- deterministic across nodes
- serializable into canonical state and result shapes
- meterable with bounded resource usage
- explicit at the host boundary
- simple enough to audit
- useful enough to justify permanent protocol surface

The old Python VM forced some restrictions because CPython itself was risky.

The new Xian VM removes much of that pressure, but it does not remove the real
blockchain constraints:

- consensus determinism
- DoS resistance
- state encoding
- metering
- semantic clarity

That means the expansion rule is now:

- not "safe inside Python"
- but "safe as protocol surface"

## Current Position

The current branch now has:

- Python-vs-`xian_vm_v1` conformance tests for the supported contract-language
  surface
- a coverage gate for all public env exports
- a coverage gate for all non-excluded allowed builtins
- explicit exclusions instead of implicit gaps

The current explicit exclusions are:

- literals/tokens rather than callable builtins:
  - `True`
  - `False`
  - `None`
  - `import`
- binary-value surface not yet modeled end to end:
  - `bytes`
  - `bytearray`
- higher-order lazy iterator surface not yet modeled end to end:
  - `map`
  - `filter`

These are not "forgotten".

They are excluded because they need deliberate VM/value-model design rather
than small interpreter patches.

## Expansion Buckets

### Bucket A: Add Soon

These are high-value and low-risk because they mostly extend deterministic
value semantics that already exist in the VM.

Candidates:

- more string helpers:
  - `split`
  - `strip`
  - `upper`
  - `endswith`
  - `find`
- more dict helpers:
  - `pop`
  - membership/iteration convenience probes where semantics are explicit
- more list helpers:
  - `index`
  - `count`
  - `clear`
  - `copy`
- more pure builtin helpers:
  - selected scalar helpers if still missing from the VM after conformance
    widening
- more deterministic syntax:
  - `for/while ... else`
  - more destructuring edge cases
  - more comparison and boolean edge cases

Why these belong here:

- no new ambient capability
- straightforward to meter
- straightforward to serialize
- easy to differential-test against the Python control path

### Bucket B: Add After Value-Model Design

These are useful, but they need an explicit protocol-level representation and
cannot be treated as "just another Python object".

Candidates:

- `bytes`
- `bytearray`
- `set`
- `frozenset`

Required design work:

- canonical runtime representation
- canonical JSON/state/result encoding
- deterministic semantics for ordering-sensitive operations
- explicit conformance rules for equality, hashing, membership, and repr
- metering rules for large-value behavior

Important point:

The new VM makes these possible.

It does **not** make them free.

For example, `set` is no longer dangerous because of CPython escape risk, but
it is still a bad protocol feature unless we define:

- how it is encoded
- how it is compared
- how it is represented in events/results/state
- whether any iteration order is observable

So these should be added only after the value model is written down first.

### Bucket C: Add After Callable/Iterator Design

These are useful, but they require a clearer first-class callable and iterator
model than the VM currently exposes.

Candidates:

- `map`
- `filter`

Required design work:

- whether the language should support lazy iterators at all
- whether the result type is lazy or eagerly materialized
- how function references are represented and called
- how metering applies to deferred work
- how the Python control path and native VM stay aligned

Recommendation:

- if we add them, prefer eager deterministic semantics first
- do not introduce a half-implicit lazy iterator model casually

### Bucket D: Keep Banned

These should remain outside the contract language unless there is a very strong
reason and a dedicated design effort.

Candidates:

- `eval`
- `exec`
- arbitrary reflection/introspection
- arbitrary filesystem/network/process access
- generic dynamic imports beyond the explicit contract import surface
- ambient global-state mutation outside explicit host APIs

Why:

- poor auditability
- poor determinism
- poor metering clarity
- unnecessary protocol surface

## Recommended Order

### 1. Finish cheap deterministic ergonomics

Do first:

- Bucket A string/list/dict helpers
- more syntax/edge-case conformance probes

This gives a lot of developer value for low protocol risk.

### 2. Design a binary value model

Do next:

- `bytes`
- `bytearray`

Reason:

- they unlock useful hashing/serialization patterns
- they are more broadly valuable than sets
- they force the shared encoding model to become more explicit

### 3. Decide whether sets are worth protocol surface

Only after binary/value-model work:

- `set`
- `frozenset`

Reason:

- they are convenient
- but less essential than binary values
- and they are easy to get subtly wrong from a determinism/encoding standpoint

### 4. Decide whether higher-order iterators belong at all

Last:

- `map`
- `filter`

Reason:

- they are nice, but not essential
- they require more semantic machinery than they first appear to

## Recommended Process For Every New Feature

For each feature:

1. write the semantics down first
2. add it to the conformance manifest
3. add Python-vs-VM differential cases
4. add replay-derived or authored-contract probes if relevant
5. only then merge it into the public contract surface

This keeps the language expansion deliberate instead of accidental.

## Concrete Next Implementation Slice

If the goal is maximum value with low risk, the next slice should be:

1. string helper expansion
2. list/dict helper expansion
3. edge-case conformance widening

If the goal is maximum capability expansion, the next slice should be:

1. binary value model (`bytes` / `bytearray`)
2. then deterministic set/frozenset design

My recommendation is the first path, then the second.

That is the best balance of utility, risk, and implementation cost.
