# Xian VM Parallel Execution Plan

## Goal

Replace the current speculative process-pool executor with a parallel execution
model that is:

- deterministic
- measurably faster than serial execution
- secure under adversarial workloads
- simple enough to reason about and operate

## Roadmap Decision (November 2026)

A profile of revision-10 execution changed the order of work. The Rust VM is
not the bottleneck; the Python host around it is, and the same costs cap every
parallel design. The roadmap is therefore:

| Step | What | Status |
|---|---|---|
| A | Serial host speedups: copy-on-write (or journaled) block-state snapshots instead of `deepcopy`, and a parsed-IR cache keyed by content hash | doing now |
| B | Move the per-transaction block loop into Rust (`execute_block`): Rust-side LMDB reads and block overlay, fee reservation/settlement and reward deltas in Rust, GIL released | doing now |
| C | Block-STM-style multi-threading in Rust over multi-version state | deferred |

Parallel mode stays disabled by default meanwhile (Phase 0 below). The
process-pool executor gets no further tuning.

### Measurements behind the decision

Apple M1 (4 performance + 4 efficiency cores), real `Xian` app, signed
transactions, metered fees and rewards on, `finalize_block` plus `commit`;
machine was shared, so ratios matter more than absolute numbers.

Serial cost per transaction in a 200-transaction block:

| | Transfer | DEX swap | CPU loop (3000 iterations) |
|---|---|---|---|
| Total | 6.4 ms | 35 ms | 7.3 ms |
| Block-state snapshot + restore (`deepcopy`) | 2.2 ms (about 12 ms at 1000 tx) | 6.4 ms | 1.5 ms |
| `execute_bundle` (Rust) | 1.8 ms, about 1.1 ms of it IR parse and validation | 19 ms | 4.8 ms of real interpretation |
| Python IR JSON load and dump | about 1.4 ms | 3.9 ms (`load_module_ir` 32 times per swap) | small |

- The state copy grows with block size: a 1000-transfer block ran at about
  65 tx/s.
- Contract IR is re-read, parsed in Python, re-serialized and parsed and
  validated again in Rust on every call, uncached: 69 KB for `currency`,
  about 320 KB each for `con_dex` and `con_pairs`. Native sampling of a DEX
  swap: serde_json 26%, module parse 12%, IR validation 8%, IR cloning about
  12%, module instantiation 14%; interpretation is a small share.

What-if for step A (benchmark-only patch: shallow snapshot plus cached Python
IR parse and serialization; app hash identical to unpatched):

| Workload | Before | After | Gain |
|---|---|---|---|
| Transfers, 1000 per block | 64.6 tx/s | 331.6 tx/s | 5.1x |
| DEX, one hot pair | 28.7 tx/s | 48.8 tx/s | 1.7x |
| CPU-heavy | 138 tx/s | 172 tx/s | 1.25x |

Caching the Rust-side parse as well is expected to bring DEX to about 2-3x
(estimate, not measured).

Current process-pool parallel mode (200-transaction blocks, tx/s; all runs
matched the serial app hash):

| Workload | Serial | 1 worker | 2 | 4 | 8 |
|---|---|---|---|---|---|
| Transfers, distinct accounts | 156 | 241 | 378 | 662 | 758 |
| CPU-heavy, independent | 138 | 128 | 138 | 126 | 139 |
| Mix, 30% DEX | 66 | 61 | 62 | 67 | 66 |
| DEX, one hot pair | 28.7 | 31 | 31 | 30 | 31 |

- Against serial with the step-A fixes (332 tx/s at 1000 per block), four
  workers are only about 2x faster and eight are slower than four: the serial
  merge in the main process and the efficiency cores cap it.
- With access estimates on (the default), only hard-coded transfer/approve
  shapes form waves, so DEX, CPU-heavy and mixed blocks run serially. Turning
  estimates off makes contended workloads worse (199 of 200 DEX transactions
  rejected).

### Why step C waits

- Today threads cannot help: `execute_bundle` holds the GIL for the whole
  call, every storage read, `contract.*`, `random.*`, `zk.*` and deploy goes
  through Python callbacks, and `rt.env`, the random state and the zk proof
  cache are process-global. Step B removes these from the hot path; Block-STM
  before B would only parallelize Python callbacks.
- Expected gain of C is about linear in cores for independent work and about
  zero on hot contracts such as one DEX pair, which degrade to serial plus
  wasted work. A and B help every workload.
- C is the most expensive and riskiest step (about 1-3 months). Revisit it
  after A and B land and are re-measured, and only if real block sizes and
  traffic justify it. Its constraints stay as below: results equal to serial
  block order, fees/rewards/counters as additive deltas, no proposer hints,
  nothing dependent on scheduling.
- Open check carried into A: confirm IR parsing is never charged to chi, so
  an IR cache cannot change chi or receipts.

Steps A and B must keep receipts, chi, `ContractingDecimal` rounding, error
texts, event order and the sorted write list byte-identical; prove it with the
determinism corpus, a parity corpus and app-hash replay.

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

The access-spec phases below remain the target design for scheduling, but
they start only after steps A and B of the roadmap decision above, which come
first.

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

Steps A and B of the roadmap decision come first. After they are measured:

1. Define the access-spec schema for exported contract functions.
2. Identify the first contract families that can support it cleanly:
   - currency-style balance updates
   - token approvals/transfers
   - note/output records
3. Build a planner prototype that stages transactions from declared accesses
   before execution.
4. Compare staged scheduling against current serial execution before writing a
   full Rust parallel executor.
