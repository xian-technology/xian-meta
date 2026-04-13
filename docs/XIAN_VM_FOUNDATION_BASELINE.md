# Xian VM Foundation Baseline

## Status

Implementation baseline for the first Xian VM groundwork slice.

This document records what now exists in code, what the first compiler-side
subset currently freezes, and how the authored contract corpus now maps to that
subset.

## What This Slice Added

### 1. Compiler-side VM compatibility profile

`xian-contracting` now has an explicit `xian_vm_v1` compatibility checker and
an audit script:

- `contracting.compilation.vm`
- `scripts/audit_vm_compatibility.py`

This is not the VM itself.

It is the first formal frontend gate for checking whether authored contracts fit
the currently frozen `xian_vm_v1` subset.

### 2. Explicit execution-policy shape in node config

`xian-abci` now writes and reads an explicit execution-policy object under:

```toml
[xian.execution.engine]
mode = "python_line_v1"
bytecode_version = ""
gas_schedule = ""
authority = ""
shadow_tracer_mode = ""
```

Current tracer-backed engines continue to run exactly as before:

- `python_line_v1`
- `native_instruction_v1`

`xian_vm_v1` is now a named future execution policy slot in config shape, and
`xian-abci` now routes it through an explicit execution-runtime probe instead of
rejecting it as an unknown future string.

Current behavior is still deliberately strict:

- current tracer-backed engines continue to run normally
- `xian_vm_v1` now performs native capability probing against `xian-vm-core`
- `xian_vm_v1` now requires an explicit `authority` choice:
  - `authority = "python"` keeps Python authoritative and runs the native VM
    in shadow for comparison
  - `authority = "native"` makes the native VM authoritative
- `shadow_tracer_mode` is now optional when `authority = "native"`:
  - in `authority = "python"` it is still required, because native execution is
    only meaningful if Python remains available as the explicit comparison path
  - in `authority = "native"` it is an optional rollout-time Python comparison
    backend; native execution and native metering can now run without it
- the node does not silently “try native first and fall back to Python” for
  consensus execution; native execution remains an explicit rollout mode, not
  an invisible fallback

That keeps the runtime honest while still moving execution selection away from a
forever-implicit `tracer_mode` string.

### 3. Structural Xian IR and host-binding catalog

`xian-contracting` now has a first structural IR contract for the frozen
frontend subset:

- `contracting.compilation.ir`
- `contracting.compilation.lowering`
- `scripts/audit_vm_ir_lowering.py`

This adds:

- a versioned IR name: `xian_ir_v1`
- a versioned host-binding catalog: `xian_vm_v1_host_v1`
- explicit lowering from validated Python AST into structural JSON IR
- an inventory of used host bindings per contract module

The important design choice here is that the VM boundary is now explicit before
runtime work begins. The Rust side no longer needs to infer semantics from
Python runtime behavior.

### 4. First Rust-side VM foundation crate

`xian-contracting/packages/xian-vm-core` is now the first Rust-side consumer of
the IR.

Current scope:

- deserialize emitted IR JSON
- validate top-level invariants
- validate recursive statement and expression node shapes
- instantiate a VM module from validated IR
- execute a first direct-IR interpreter slice for:
  - local assignments and returns
  - `Variable.get()` / `Variable.set()`
  - `Hash` reads, writes, and `+=` / `-=` style mutation
  - arbitrary-precision integer values instead of `i64`-only VM integers
  - fixed-precision `decimal(...)` construction and arithmetic
  - native `datetime.datetime` / `datetime.timedelta` values, including
    `datetime.datetime.strptime(...)`, arithmetic, comparison, and field access
  - bigint-oriented builtins needed by the shielded contracts, including:
    - `int(..., base)`
    - `pow(base, exp, mod)`
    - `format(value, "064x")`
  - `hashlib.sha3(...)` and `hashlib.sha256(...)`
  - `crypto.verify(...)` and `crypto.key_is_valid(...)`
  - `LogEvent` emission
  - native collection helpers used by the current corpus:
    - `dict.keys()` / `dict.values()` / `dict.items()` / `dict.get()`
    - `list.append()` / `list.extend()` / `list.insert()` / `list.remove()` / `list.pop()`
    - Python-style slicing for `list` / `tuple` / `str`
    - sequence repetition for `list` / `tuple` / `str`
    - builtins `sorted`, `sum`, `min`, `max`, `all`, `any`, `reversed`, and
      `zip`
  - native string helpers used by the shielded contracts:
    - `lower(...)`
    - `isalnum(...)`
    - `startswith(...)`
    - `join(...)`
  - imported contract export calls
  - dynamic-import / factory-handle contract export calls
  - host-delegated `zk.*` syscalls, which stay explicit host operations instead
    of being reimplemented inside the Rust runtime

The important change is that Rust is no longer only validating the compiler
contract. It is now executing a bounded but real subset of `xian_ir_v1`
directly.

It also now exposes a minimal Python-facing native surface through
`xian_vm_core._native` so node-side code can:

- read runtime capability metadata
- validate emitted module IR
- check whether a configured bytecode/gas policy is supported

### 5. Opt-in `xian-abci` execution-runtime path

`xian-abci` now has a real execution-engine boundary instead of only startup
probing:

- `TxProcessor` preflights the target contract through the native VM frontend
  when `xian_vm_v1` is enabled
- readonly simulation workers do the same preflight before executing the Python
  path
- explicit simulation requests support both rollout modes:
  - `authority = "python"`: Python authoritative, native shadow
  - `authority = "native"`: native authoritative, Python comparison
- real transaction processing now supports both rollout modes on the
  authoritative tx path:
  - `authority = "python"`: Python authoritative, native shadow
  - `authority = "native"`: native authoritative, Python comparison
- speculative parallel workers carry the same execution-runtime configuration,
  so shadow-mode preflight is consistent across serial and parallel execution

The native path is now materially more self-contained than the earlier slices:

- authored contract submission and governed `__source__` patches now persist
  `__xian_ir_v1__` alongside `__source__` and `__code__`
- the Python VM host and the `xian-abci` preflight path now require persisted
  `xian_ir_v1` for `xian_vm_v1` execution; stored `__source__` remains
  inspection/debug metadata and is no longer an execution fallback
- the built-in `submission` contract now seeds a dedicated authored-source
  companion, so genesis/client bootstrapping persists `submission.__source__`
  and `submission.__xian_ir_v1__` as first-class artifacts instead of leaving
  it as runtime-code-only state
- the authored contract bundles in `xian-configs` do not need special casing;
  they already inherit persisted source and IR through the normal submission
  path
- the native host now models contract-management side effects explicitly for
  `submission`-style flows, including deploy, owner changes, and developer
  changes, and returns those staged writes/events as part of native execution
- native deployment is now artifact-driven end to end:
  - the native host validates `deployment_artifacts`
  - it stages contract metadata/code/source/IR writes directly
  - it executes child constructors natively instead of delegating deploy-time
    contract execution back through Python `Contract.deploy(...)`
- native deployment no longer has a local-time fallback:
  if deterministic `now` context is missing, deployment fails explicitly
  instead of reading wall-clock time from the host machine
- artifact validation on the native deployment path now runs in Rust and
  rejects malformed or internally inconsistent bundles, including IR/source
  hash mismatches
- canonical source-to-runtime recompilation is still provided by the Python
  artifact validator used by the Python deployment path and offline tooling,
  so the native path is Rust-native for bundle validation but not yet a full
  Rust recompiler
- `xian_vm_v1` rollout now enforces artifact-backed deployment even in
  `authority = "python"` shadow mode, so source-only submissions are rejected
  instead of creating state that native-authority mode would later refuse
- the remaining live on-chain factory flow, `token_factory`, now materializes
  and submits canonical child deployment artifacts, so native-authority
  contract creation is no longer limited to direct client submissions
- `authority = "native"` no longer depends on Python for chi accounting or
  contract reward weights, and it no longer requires Python shadow comparison
  to be configured
- `xian-stack` now exposes a first-class `make localnet-vm-e2e` path that
  boots a 5-node integrated localnet with `xian_vm_v1` in native-authority
  mode plus Python shadow comparison for soak and replay-style validation
- the current native-authority soak baseline is no longer theoretical:
  `make localnet-vm-e2e` now completes the full 16-phase run successfully,
  including shielded-note-token and parallel prefix-scan workloads
- `xian-abci` now also ships an explicit legacy-network replay audit tool:
  `xian-legacy-replay-audit`
  - it seeds local replay state from the legacy chain `GENESIS`
    pseudo-transaction exposed through BDS GraphQL
  - it reads ordered transactions and finalized tx results from CometBFT RPC
    block data instead of relying on the legacy BDS ordering model
  - it distinguishes strict historical parity from logic parity, so
    metering/reward drift is visible without hiding whether current Python or
    `xian_vm_v1` can still execute the same contract call path
  - it also supports a `--logic-only` mode for “can the new VM still process
    this old successful transaction path?” audits where exact legacy fee
    economics are not the target
  - it also supports a `--native-only` mode so large historical audits can
    focus directly on VM readiness without paying the extra Python control-path
    cost on every transaction
  - it writes a structured replay report plus a normalized transaction log for
    later widening from small audit windows to larger historical ranges
- VM rollout observability is now first-class instead of log-only:
  - `xian-abci` exports shadow/native comparison counters and latest-mismatch
    context through Prometheus metrics
  - mismatch records are appended to
    `storage/logs/xian-vm-shadow-mismatches.jsonl`
  - `xian-stack/scripts/localnet_vm_rollout.py` collects those signals from a
    running localnet and summarizes rollout consistency as JSON
  - localnet now exposes the Xian app metrics exporter separately from the
    CometBFT metrics port, so rollout validation reads the actual VM metrics
  - `make localnet-vm-e2e` now writes `vm_rollout.json` and fails by default if
    the mismatch budget is exceeded
  - the main monitoring stack now ships VM-specific alert rules and a dedicated
    Grafana dashboard (`Xian VM Runtime`) in addition to summary panels on the
    existing overview/preset dashboards
  - the monitoring stack also now ships a dedicated `Xian BDS Recovery`
    dashboard plus Alertmanager routing examples so VM mismatch alerts and BDS
    recovery alerts can be separated operationally
- `token_factory.s.py` is now rendered from a clean template plus generated
  artifact block, so the large child-contract artifact payload is derived
  output rather than hand-maintained contract source

It is now a real engine boundary with an explicit authoritative native mode,
not only a shadow probe path.

### 6. Explicit VM metering and corpus calibration

`xian-vm-core` no longer uses the earlier placeholder meter shape.

Current native metering now includes:

- storage reads in the VM host path
- storage writes in the VM host path
- transaction-byte charging
- return-value charging
- an explicit `xian_vm_v1` gas schedule over statements, expressions, call
  dispatch, and loop iterations
- first-load module initialization, including global declarations and module
  body execution

There is also now a calibration audit:

- `xian-contracting/scripts/audit_vm_metering.py`

That audit runs the full authored parity corpus through both:

- Python `native_instruction_v1`
- Rust `xian_vm_v1`

and reports the current ratio envelope, instead of treating metering as a
placeholder.

Current calibration state on this branch:

- no fixture in the current parity corpus is under-metered relative to
  `native_instruction_v1`
- the authored-contract subset currently lands in roughly the `1.02x` to
  `2.35x` band versus `native_instruction_v1`
- the full mixed corpus, including intentionally synthetic helper fixtures,
  currently lands in roughly the `1.02x` to `2.50x` band

The native Python host bridge was tightened here too, so `contract.exists(...)`,
`contract.has_export(...)`, `contract.info(...)`, and related metadata syscalls
now resolve directly against the driver / lowered IR in the native host path
instead of depending on Python runtime globals.

### 7. Curated Python-runtime parity fixtures

`xian-vm-core` now has committed parity fixtures generated from the current
Python runtime and checked from Rust:

- `packages/xian-vm-core/tests/fixtures/transfer_event.json`
- `packages/xian-vm-core/tests/fixtures/range_summary.json`
- `packages/xian-vm-core/tests/fixtures/foreign_state_probe.json`
- `packages/xian-vm-core/tests/fixtures/decimal_arithmetic.json`
- `packages/xian-vm-core/tests/fixtures/collection_helpers.json`
- `packages/xian-vm-core/tests/fixtures/time_hash_crypto.json`
- `packages/xian-vm-core/tests/fixtures/bigint_shielded_primitives.json`
- `packages/xian-vm-core/tests/fixtures/authored_shielded_note_hash.json`
- `packages/xian-vm-core/tests/fixtures/authored_shielded_commands_hash.json`
- `packages/xian-vm-core/tests/fixtures/authored_currency_transfer.json`
- `packages/xian-vm-core/tests/fixtures/authored_stable_token_burn.json`
- `packages/xian-vm-core/tests/fixtures/authored_reflection_transfer.json`
- `packages/xian-vm-core/tests/fixtures/authored_profile_channel.json`
- `packages/xian-vm-core/tests/fixtures/authored_turn_based_join.json`
- `packages/xian-vm-core/tests/fixtures/authored_oracle_price_info.json`
- `packages/xian-vm-core/tests/fixtures/authored_members_reward_change.json`
- `packages/xian-vm-core/tests/fixtures/authored_dex_swap_path.json`
- `packages/xian-vm-core/tests/parity_fixtures.rs`
- `scripts/generate_vm_parity_fixtures.py`

These fixtures currently compare:

- return values
- final local storage values
- foreign storage reads
- decimal serialization and arithmetic semantics
- native collection-helper behavior
- datetime/timedelta behavior
- bigint parsing, modular arithmetic, hex formatting, and shielded-style helper
  flows
- hashing and ed25519 verification behavior
- emitted event payload shape, including indexed vs non-indexed fields
- nested imported-contract context propagation
- real authored shielded contract helper execution, including:
  - constructor-seeded module state snapshots
  - `shielded-note-token.hash_relay_transfer(...)`
  - `shielded-commands.hash_command(...)`
  - importlib-based target/export checks in the command path
- broader authored contract execution across repos, including:
  - currency transfer semantics on genesis token state
  - stable-token burn and metadata/supply sync
  - reflection-token transfer semantics
  - profile-registry setup-plus-create-channel flows
  - turn-based-games setup-plus-join flows
  - oracle reporter/config setup plus median-price reads
  - members/rewards/currency governance path setup plus vote proposal flow
  - DEX add-liquidity plus swap execution against real token contracts

This is still not full-contract parity, but it is no longer limited to purely
synthetic fixtures. The parity path now includes real authored shielded module
sources and broader authored app/token modules on top of the earlier curated
subset, replacing “trust the hand-written Rust unit tests” with a real snapshot
path from the existing Python executor.

### 8. Explicit runtime host operations in IR

The IR now makes the highest-value runtime operations explicit instead of
leaving them as generic Python attribute/subscript behavior.

Current explicit runtime operations include:

- storage reads and writes for `Hash` / `ForeignHash`
- `Variable.get()` / `Variable.set()`
- event emission through declared `LogEvent` bindings
- time construction and parsing through:
  - `datetime.datetime(...)`
  - `datetime.datetime.strptime(...)`
  - `datetime.timedelta(...)`
- bigint-heavy numeric operations through:
  - large integer constants serialized safely in IR JSON
  - `int(..., base)`
  - `pow(base, exp, mod)`
  - `format(value, "064x")`
- hashing helpers through:
  - `hashlib.sha3(...)`
  - `hashlib.sha256(...)`
- ed25519 helpers through:
  - `crypto.verify(...)`
  - `crypto.key_is_valid(...)`
- direct contract export calls through:
  - static `import contract_name`
  - `importlib.import_module(...)`
  - local handle wrappers that return imported contract modules
- zk host-boundary calls, which are lowered explicitly and delegated through the
  VM host surface instead of being folded back into implicit Python runtime
  behavior

That means the Rust runtime no longer has to reverse-engineer the meaning of
operations like:

- `balances[account]`
- `balances[account] += amount`
- `metadata.set(now)`
- `currency.transfer(...)`
- `token.transfer(...)` where `token` came from `importlib.import_module(...)`
- `datetime.datetime.strptime(...)`
- `hashlib.sha3(...)`
- `crypto.verify(...)`
- `zk.shielded_output_payload_hash(...)`
- `pow(state, 7, FIELD_MODULUS)`
- `"0x" + format(value, "064x")`
- `"".join(items)` and `value.startswith("0x")`
- `value[2:]`

## Frozen Frontend Decisions In This Slice

The current `xian_vm_v1` compatibility profile currently makes these decisions:

- Python remains the authoring language frontend.
- Current contract lint rules still apply first.
- `while` loops are allowed and executed natively.
- list and dict comprehensions are allowed and executed natively.
- generator expressions remain outside the contract language because they are
  still illegal in the shared Python Contracting surface.
- set literals, set comprehensions, and `set` / `frozenset` builtins are now
  explicitly banned in the shared contract language rather than being
  VM-specific restrictions, because the common runtime/state encoding surface
  does not yet define a safe canonical representation for them.
- `list` and `dict` remain first-class allowed value types.
- helper usage such as `len`, `range`, `sorted`, `sum`, `min`, `max`, `all`,
  and `any` is inventoried for future narrowing decisions.
- the current widened conformance matrix now also covers all public env exports
  and all non-excluded allowed builtins; the remaining explicit exclusions are
  `bytes`, `bytearray`, `map`, and `filter`, which need dedicated value-model
  or higher-order iterator design before they should become part of the
  permanent contract surface

This is still intentionally conservative, but it is now a contract-language
decision rather than only a VM-internal subset freeze.

The point is to freeze a real first subset, run it against the authored
contract corpus, and surface the exact blockers instead of leaving the subset
entirely aspirational.

## Baseline Audit Result

Audit command:

```bash
uv run --project ../xian-contracting python ../xian-contracting/scripts/audit_vm_compatibility.py \
  ../xian-contracts/contracts \
  ../xian-configs/contracts \
  ../xian-configs/solution-packs/stable-protocol/contracts \
  ../xian-stable-protocol/contracts
```

Current result for authored contract sources:

- files scanned: `40`
- compatible now: `40`
- incompatible now: `0`

Feature counts from that audit:

- `len_calls`: `127`
- `range_calls`: `23`
- `sorted_calls`: `2`
- `sum_calls`: `1`
- `dict_literals`: `894`
- `list_literals`: `116`
- `list_calls`: `2`
- `max_calls`: `1`
- `min_calls`: `1`

## IR Lowering Audit Result

Lowering command:

```bash
uv run --project ../xian-contracting python ../xian-contracting/scripts/audit_vm_ir_lowering.py \
  ../xian-contracts/contracts \
  ../xian-configs/contracts \
  ../xian-configs/solution-packs/stable-protocol/contracts \
  ../xian-stable-protocol/contracts
```

Current result for authored contract sources:

- files scanned: `40`
- lowered now: `40`
- failed now: `0`

Representative host-binding usage from that audit:

- `storage.hash.new`: `34`
- `storage.variable.new`: `28`
- `event.log.new`: `28`
- `event.log.emit`: `28`
- `storage.variable.get`: `28`
- `storage.variable.set`: `28`
- `storage.hash.get`: `33`
- `storage.hash.set`: `33`
- `contract.import`: `21`
- `contract.export_call`: `27`
- `env.now`: `22`
- `context.caller`: `34`
- `numeric.decimal.new`: `17`
- `zk.verify_groth16`: `2`

## Corpus Alignment Result

The authored contract corpus used in the audit is now fully inside the frozen
`xian_vm_v1` compatibility profile.

The rewrites in this branch removed the previously incompatible constructs from:

- `xian-contracts/contracts/profile-registry/src/con_profile_registry.py`
- `xian-contracts/contracts/shielded-commands/src/con_shielded_commands.py`
- `xian-contracts/contracts/shielded-note-token/src/con_shielded_note_token.py`
- `xian-contracts/contracts/turn-based-games/src/con_turn_based_games.py`
- `xian-configs/contracts/members.s.py`
- `xian-configs/contracts/rewards.s.py`
- `xian-configs/solution-packs/stable-protocol/contracts/oracle.s.py`
- `xian-stable-protocol/contracts/oracle.s.py`

## What This Means

The first VM subset is now large enough to cover the current authored contract
corpus that was audited in this slice.

That matters because the next VM steps can now target a real, corpus-backed
frontend surface instead of a speculative one.

It also means Rust work is now justified, but only below the frozen IR
boundary. The immediate numeric blocker is no longer the main issue. The right
order is now:

1. keep the frontend subset and IR contract stable
2. keep expanding authored parity fixtures and setup-driven execution scenarios
   across the real contract corpus
3. execute `xian_ir_v1` directly in Rust before introducing a separate
   bytecode layer
4. move more execution semantics into Rust against that contract
5. build parity and metering validation around the Rust runtime

The parity portion now spans a broader authored subset. The next task is to
keep widening that execution surface and use the failures to decide which host
operations should stay delegated.

## Next Useful Steps

1. Extend the direct-IR Rust interpreter from the current bounded slice into
   broader contract coverage:
   - more builtin coverage
   - `ForeignVariable` / `ForeignHash` parity
   - richer container operations
   - decimal and datetime behavior
2. Expand parity execution tests around the now-lowered authored contract corpus
   and compare:
   - state writes
   - setup-call state transitions
   - emitted events
   - `ctx.signer` / `ctx.caller`
   - return values
   - decimal behavior
   - chi accounting
   - imported contract calls
3. Move from shadow preflight into a true native transaction executor in
   `xian-abci` once parity is credible enough for state-write comparison.
4. Only introduce an internal bytecode layer later if the direct-IR interpreter
   proves to be a real bottleneck or prevents specific optimizations.
