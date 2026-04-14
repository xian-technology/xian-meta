# Xian VM Parallel Execution Plan

## Goal

Replace the current speculative process-pool executor with a parallel execution
model that is:

- deterministic
- measurably faster than serial execution
- secure under adversarial workloads
- simple enough to reason about and operate

## Current Diagnosis

The current `parallel_execution` path is correct but not performant enough to
justify being enabled by default.

Observed behavior from the current VM branch benchmarks:

- native VM transaction execution is already relatively cheap
- `track_access=True` adds only a small serial overhead
- the slowdown sits mainly in block-level `finalize_parallel`
- accepted speculative execution still loses to serial execution

This means the bottleneck is not the VM interpreter. It is the orchestration
model around it.

## Why The Current Model Loses

The current design speculates by running transactions in separate spawned worker
processes, with copied pending writes and per-task cache resets. That means
Xian pays for:

- process creation and IPC semantics
- repeated state snapshot shipping
- repeated cache flush/reset cycles
- repeated result merging into the authoritative process

This cost is structural. It remains even when speculation succeeds and fallback
is not triggered.

## Design Constraints

Any replacement must preserve:

- block-order determinism
- exact same final state on every validator
- explicit metering
- explicit host-boundary control
- safe handling of shared hot state

Parallelism must never rely on non-deterministic scheduling outcomes.

## Recommended Direction

### 1. Access-Spec-Driven Scheduling

Make parallelism an artifact of contract metadata, not speculative execution.

For exported functions, add deterministic access specs to the contract artifact
/ IR that describe:

- exact reads
- exact writes
- prefix reads
- additive/commutative writes
- dynamic cases that require serialization

Given transaction arguments, the node should derive the concrete state keys
before execution and build deterministic conflict-free stages.

If a function cannot provide a safe access spec, it runs serially.

This is the best medium-term fit for Xian.

### 2. Rust-Side Shared-State Executor

Once access specs exist, move the parallel execution engine away from the
current process-pool model and toward a shared in-memory executor in Rust.

That executor should:

- use threads, not child processes
- operate over a shared block-scoped state overlay
- apply writes only after deterministic stage completion
- keep the Python host boundary out of the hot path as much as possible

### 3. Commutative Write Classes

Expand the existing additive-write model for cases where order does not affect
the mathematical result, for example:

- reward accumulators
- fee pools
- counters
- other merge-safe deltas

This reduces unnecessary serialization while preserving determinism.

### 4. Shared-State Classification

Classify hot state prefixes explicitly.

Examples:

- likely parallelizable:
  - per-account balances
  - per-item / per-profile state
  - disjoint note/output records
- likely serialized:
  - DEX pair reserves
  - governance proposal tallies
  - validator-set and epoch-global state

This gives Xian a simpler and safer scheduling boundary even before a full
MVCC engine exists.

## What Not To Do

Do not keep investing heavily in the current speculative process-pool executor.

Small optimizations there may reduce waste, but they do not change the core
problem: the system is parallelizing by duplicating runtime work and moving
state between processes.

That is the wrong shape once VM execution itself becomes fast.

## Phased Implementation Plan

### Phase 0: Safe Default

- keep `parallel_execution` disabled by default
- keep opt-in support for localnet experiments and benchmark profiles
- keep current profiling counters so regressions stay visible

### Phase 1: Access-Spec IR Design

Add an explicit access-spec section to `xian_ir_v1` or its next compatible
revision.

Required output per exported function:

- key templates for reads
- key templates for writes
- prefix-read templates
- additive-write templates
- serialization flag when access cannot be described safely

Open question:

- whether specs are authored manually, compiler-derived, or hybrid

Recommendation:

- start hybrid
- compiler derives what it can
- contract authors may explicitly refine only when needed

### Phase 2: Deterministic Pre-Execution Planner

Given a block and decoded tx args:

- derive concrete keys from access specs
- build deterministic parallel stages before execution
- keep block order as the canonical serialization order
- reject or serialize transactions whose runtime access escapes the declared
  envelope

### Phase 3: Runtime Validation

During execution:

- track actual accesses
- compare them to declared accesses
- on mismatch, fail deterministically or force the function class to remain
  serial-only depending on rollout mode

This is mandatory for safety. Access specs must never be trusted blindly.

### Phase 4: Rust Shared Overlay

Implement a block-scoped shared state overlay in Rust:

- read through committed state + prior stage writes
- collect stage-local writes without process copies
- merge completed stage writes deterministically

The initial implementation can be stage-parallel without full MVCC.

### Phase 5: Additive Write Support

Make additive writes first-class in the scheduler and overlay:

- do not serialize two transactions just because both contribute to the same
  merge-safe accumulator
- require clear merge semantics and tests per additive class

### Phase 6: Optional MVCC / Block-STM Evolution

Only after the above lands and is measured:

- consider a true multi-version executor
- validate whether the extra complexity produces material wins over staged
  access-spec scheduling

This is a long-term optimization, not the first fix.

## Security Requirements

Any new parallel executor must satisfy:

- same final state as preset serial block order
- same events and result semantics
- deterministic handling of invalid access specs
- no proposer-controlled scheduling hints
- no hidden read/write behavior outside validated host calls
- no cross-thread races that can alter committed state

Parallelism must be a local execution optimization only.

## Rollout Strategy

1. Keep default serial execution.
2. Add access-spec IR and validation without parallel execution.
3. Add deterministic staged parallel execution behind explicit opt-in.
4. Benchmark against serial on:
   - transfer fanout
   - heavy contract execution
   - DEX-like workloads
   - governance/epoch workloads
5. Enable by default only when it is consistently faster and mismatch-free.

## Success Criteria

The new design is good enough when all of these are true:

- parallel mode beats serial mode on the representative benchmark suite
- gains survive on both light and heavy workloads
- no determinism mismatches appear in localnet soak runs
- fallback/serialization behavior is explicit and observable
- hot-state contention does not collapse performance unpredictably

## Immediate Next Tasks

1. Define the access-spec schema for exported contract functions.
2. Identify the first contract families that can support it cleanly:
   - currency-style balance updates
   - token approvals/transfers
   - note/output records
3. Build a planner prototype that stages transactions from declared accesses
   before execution.
4. Compare staged scheduling against current serial execution before writing a
   full Rust parallel executor.
