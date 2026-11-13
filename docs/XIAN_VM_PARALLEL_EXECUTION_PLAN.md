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
| A | Serial host speedups: copy-on-write (or journaled) block-state snapshots instead of `deepcopy`, and a parsed-IR cache keyed by content hash | landed (see below) |
| B | Move the per-transaction block loop into Rust (`execute_block`): Rust-side LMDB reads and block overlay, fee reservation/settlement and reward deltas in Rust, GIL released | landed (B0-B5, see below) |
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

- Before step B threads could not help: `execute_bundle` held the GIL for
  the whole call, every storage read, `contract.*`, `random.*`, `zk.*` and
  deploy went through Python callbacks, and `rt.env`, the random state and
  the zk proof cache are process-global. Step B removed these from the hot
  path (the block executor runs with the GIL released, and since B5 also
  serves hash scans and the contract metadata reads); random, zk and deploy
  still take the Python path.
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

### Step A result

Landed in xian-contracting `17fca5c5` (undo-log scope
`Driver.discarding_changes()` instead of deep-copy snapshots), `fc15e7cf`
(decoded large stored texts shared per byte-identical content) and
`bc362112` (Rust `ModuleCache`: each contract's IR parsed and validated once
per byte-identical text), and in xian-abci `f474b76` and `e68493f` (the node
uses the undo scope and reuses the per-module preparation check by IR text).
IR parsing and validation are pure and never metered, so the open check
above holds: chi, receipts, events and app hashes are byte-identical.

Throughput on revision 11, same benchmark harness, before = xian-abci
`d6631e3` with xian-contracting `654702fe`, after = `e68493f` with `bc362112`
(tx/s, two interleaved runs each, load average about 3; all runs
byte-identical in app hashes, receipts and final state):

| Workload | Before | After | Gain |
|---|---|---|---|
| Transfers, 200 per block | 141 | 564 | 4.0x |
| Transfers, 1000 per block | 62 | 574 | 9.3x |
| DEX, one hot pair, 200 per block | 29 | 137 | 4.7x |
| CPU-heavy, 200 per block | 123 | 159 | 1.3x |
| Mix, 30% DEX, 200 per block | 66 | 281 | 4.3x |
| Edge cases (same-block deploys, failures), 20 per block | 221 | 401 | 1.8x |

Per-transaction cost no longer grows with block size. Step B is the next
serial step; C stays deferred.

Steps A and B must keep receipts, chi, `ContractingDecimal` rounding, error
texts, event order and the sorted write list byte-identical; prove it with the
determinism corpus, a parity corpus and app-hash replay.

### Step B result

Step B moves the per-transaction block loop into Rust in increments; every
increment kept app hashes, receipts (including error texts), chi, fees,
refunds, reward deltas, event order and final state byte-identical (checked
with the determinism corpus, seed 20261103, and per-block app hash, receipt
digest, success count and final state on six benchmark workloads).

Landed:

| Increment | What | Commits |
|---|---|---|
| B0 | Function IR shared by handle instead of cloned per call; entry charge and lexical bindings computed once per validated module | contracting `e2e492b4` |
| Owner cache | Contract owner read once per execution, not per call | contracting `ba2bc995` |
| B0b | Module-level declarations evaluated without copying the globals per declaration | contracting `08b7df3d` |
| B1b | Rust owns the node's single LMDB environment (vendored LMDB 0.9.36); py-lmdb only in compatibility tests | contracting `d4c28cf5`, abci `a375933` |
| B1a | Rust stored-value reader; committed VM reads served from LMDB in Rust; a rejected stored value is a host fault | contracting `21bc7ee2`, `1e2127a9` |
| B2 | Block overlay in a Rust `BlockState` (pending writes as stored bytes in key order, tracked reads, one discarding scope); the driver and the node use a small explicit API; the VM reads pending and committed state in Rust; byte-identical Rust stored-value writer (prerequisite for B4) | contracting `8e69f0d2`, `b3cb041a`, `9097f065`; abci `95b4f95` |
| B3 | Fee reservation, refunds, failure metering and transaction rewards in Rust: CPython's default `decimal` context through the vendored libmpdec, `ContractingDecimal` arithmetic, reward split by validator power, commission, self bond, delegations and developer contract costs; rewards computed in Rust over node state from the Python path already | contracting `4b78c907`; abci `f566781`, `9777402` |
| B4 | `BlockExecutor`: a block's transactions run in Rust over the block overlay with the GIL released (reservation, preparation, entry checks, VM execution through the shared bundle executor with a Rust host, failure charge, refund or metering, rewards, staging through the single staging point); transactions that need Python run through `process_tx` in their place in the block | contracting `a31c6cf6`, `74296283`, `ad6bcbf1`; abci `80d5bad` |
| B5 | Hash scans and the `contract.info` / `contract.code_hash` metadata reads served by the block executor instead of handed back (see below) | contracting `707d6137`; abci `6d7bcbc` |

Throughput after B4 (revision 13), same harness as step A, tx/s, median of two
interleaved runs. The revision-12 baseline (step A only, xian-contracting
`96363368` with xian-abci `711e8c5`) and the B2 column are from the B2 and B3
measurements; B3 and B4 ran back to back (load average 3.5-4.6). Every step was
byte-identical to the one before it on every block. All bench venvs use the
native admission fastpath, as the node image does.

| Workload | Rev 12 (step A) | B2 | B3 | B4 | B4 vs rev 12 | B4 vs B3 |
|---|---|---|---|---|---|---|
| Transfers, 200 per block | 872 | 1168 | 1370 | 2067 | 2.37x | 1.51x |
| Transfers, 1000 per block | 901 | 1167 | 1480 | 2280 | 2.53x | 1.54x |
| DEX, one hot pair, 200 per block | 158 | 390 | 451 | 640 | 4.05x | 1.42x |
| CPU-heavy, 200 per block | 183 | 180 | 182 | 192 | 1.05x | 1.06x |
| Mix, 30% DEX, 200 per block | 370 | 744 | 830 | 1209 | 3.27x | 1.46x |
| Edge cases, 20 per block | 505 | 600 | 678 | 810 | 1.60x | 1.19x |

Where the gain comes from: B0-B2 sped up the VM itself and moved every state
read into Rust; B3 removed the Python reward computation (about 15% on
transfers); B4 removed the remaining Python glue per transaction (input and
output conversion, fee bookkeeping, write staging) and decodes each
contract's IR once per run instead of on every read. CPU-heavy work is pure
interpretation and stays where it was.

How B4 stays byte-identical: the Rust path covers the common shape and hands
everything else back before any of its effects reach the overlay. The node
then runs that transaction through the existing Python path, in block order,
and Rust continues after it. Handed back: contract submission, host syscalls
other than the contract metadata reads `contract.exists`,
`contract.has_export`, `contract.owner_of`, `contract.info` and
`contract.code_hash` (random, zk, deploy, metadata changes), zk modules,
owner or export rejections, preparation failures, non-numeric balances, reward inputs
the B3 port does not cover, and any write or event Python's output checks
could refuse. The reason is logged at debug level. The differential tests
(`tests/integration/test_rust_block_executor.py`, the reward and fee corpora)
and the bench (per-block app hash, receipt digest, success count and final
state on every workload) check the outcomes against the Python path.

What B4 means for the legacy process-pool parallel executor: it still works
and its configuration is unchanged, but it runs the Python per-transaction
path in its workers, which is now 1.4-1.5x slower than serial Rust execution
before any pool overhead. Enabling it would make blocks slower; it stays off
by default and gets no further work. The GIL is released for the whole Rust
run, so a thread-based scheduler (step C) is possible now without Python
callbacks in the hot path.

B5 serves hash scans (`Hash.all`, `Hash.clear`, `Hash.clone_from`,
`ForeignHash.all`, with or without a prefix) and the read-only metadata
syscalls `contract.info` and `contract.code_hash` in Rust. A scan reads the
block overlay's pending entries over one LMDB snapshot, as
`Driver.iter_items` does: a pending deletion hides the stored entry, values
are decoded as the scan reaches them, and the VM stops it when chi or the
scan allocation bound (128 KiB, 131072 entries) runs out. The metadata
syscalls also take a contract module handle, as the Python host does.

Throughput after B5 (same harness, tx/s, median of two interleaved runs,
load average 4-10; base is the B4 main). Every block was byte-identical to
B4. The new `scanmeta` workload sends 200 transactions per block that each
write two hash entries, scan a 12-entry hash group (pending and committed
entries) and call `contract.info` and `contract.code_hash`; on B4 every one
of them was handed back. Workloads without scans or metadata calls do not
change (edge cases, 20 per block: 776 and 777 over three runs).

| Workload | B4 | B5 | B5 vs B4 |
|---|---|---|---|
| Hash scans + metadata, 200 per block | 893 | 2153 | 2.41x |
| Transfers, 200 per block | 1944 | 1961 | 1.01x |
| Transfers, 1000 per block | 2116 | 2118 | 1.00x |
| DEX, one hot pair, 200 per block | 597 | 603 | 1.01x |
| CPU-heavy, 200 per block | 185 | 189 | 1.02x |
| Mix, 30% DEX, 200 per block | 1118 | 1125 | 1.01x |

Not ported yet (they run on the Python path, correctly but at Python speed):
random, deploy, the submission-only metadata changes (`contract.set_owner`,
`contract.set_developer`) and zk. Random is the next candidate if real
traffic uses it on hot paths. Porting it means: the per-transaction
`DeterministicRandom` state in the block host (cleared per transaction,
shared by nested calls), its seed material from the chain id, block number,
block hash and the transaction's input hash (`__input_hash`, which the Rust
transaction context does not carry yet) plus `aux_salt` formatted exactly
as Python's `str()` formats each VM value, the SHA3-256 counter stream with
`getrandbits` over arbitrary bit counts, `randbelow` rejection sampling,
`random()` as 53 bits over 2^53, `shuffle`, `randint`, `choice` and
`choices` with Python's error texts, and a differential corpus over all of
them.

Step B is complete. Step C (Block-STM) stays deferred: it needs multi-version
state over `BlockState`, and its gain is about zero on hot contracts such as
one DEX pair; revisit it when real block sizes and traffic justify it.

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
