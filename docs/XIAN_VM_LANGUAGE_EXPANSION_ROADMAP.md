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

The old CPython-backed execution path forced some restrictions because CPython
itself was risky.

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
- authored-contract audits that fail when real contracts use tracked feature
  families without matching conformance coverage
- exact method-level coverage for the string/list helper methods the authored
  contract corpus actually uses
- a coverage gate for all public env exports
- a coverage gate for all non-excluded allowed builtins
- explicit exclusions instead of implicit gaps
- deterministic `bytes` / `bytearray` value support
- deterministic `set()` / `frozenset()` value support with canonical encoding
- eager deterministic `map()` / `filter()` support that materializes lists in
  both engines
- authored-style differential probes for static-import reward changes and
  token-like approval/event flows
- replay-derived permanent probes for submission-style deployment/ownership
  changes and imported token event sequencing
- a DEX-style router/pair/token permanent probe for multi-module swap/event
  behavior
- a governance/state-patch permanent probe for proposal approval, imported
  execution, and patch-state persistence
- a validator-membership and epoch-reward permanent probe for operational
  network-state transitions across modules

The current explicit exclusions are:

- literals/tokens rather than callable builtins:
  - `True`
  - `False`
  - `None`
  - `import`

The current intentional syntax exclusions are:

- set literal syntax
- set comprehension syntax

Those stay banned for now because the Python control path would create native
CPython sets for that syntax, which breaks the shared deterministic contract
value model. The supported surface is constructor-based `set()` /
`frozenset()`, not raw `{...}` set syntax.

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

### Bucket B: Design Before Syntax Expansion

These are useful, but they need deeper syntax/runtime agreement than the
current shared Python/Xian-VM surface provides.

Candidates:

- set literal syntax
- set comprehension syntax

Required design work:

- a shared source-level translation or other mechanism that avoids native
  CPython set objects on the Python control path
- parity rules for comprehension semantics
- a decision on whether raw set syntax is valuable enough to justify that extra
  machinery

Important point:

The value model is now solved.

The remaining issue is not state encoding anymore. It is shared source-surface
compatibility.

### Bucket C: Add After Further Callable/Iterator Design

The low-risk higher-order helpers now exist with eager deterministic list
semantics. More advanced callable or iterator work should still wait until the
language actually needs it.

Candidates:

- lazy iterator values
- richer first-class callable values beyond local functions and builtins
- additional higher-order helpers if they justify the semantic complexity

Required design work:

- whether the language should support lazy iterators at all
- whether the result type is lazy or eagerly materialized
- how function references are represented and called
- how metering applies to deferred work
- how the Python control path and native VM stay aligned

Recommendation:

- keep `map()` / `filter()` eager
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

### 2. Decide whether set syntax is worth a source-level translation layer

Do next:

- raw set literal syntax
- set comprehension syntax

Reason:

- the deterministic value semantics already exist
- the remaining question is whether source-surface parity should grow to include
  syntax that the Python path cannot share natively

### 3. Decide whether a richer iterator model belongs at all

Last:

- lazy iterator values
- additional higher-order helpers built on that model

Reason:

- eager deterministic helpers already cover the low-risk value case
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

1. decide whether raw set syntax deserves explicit translation support
2. decide whether a real lazy iterator model is worth adding
`bytes` / `bytearray` are no longer future design work on this branch; they are
part of the implemented VM and shared contract surface now.

My recommendation is the first path, then the second.

That is the best balance of utility, risk, and implementation cost.
