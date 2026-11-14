# Rust as the single execution engine

Status: approved 2026-11-13 with all seven recommended decisions. Progress is recorded per increment below.

## Goal
Every consensus rule of a transaction exists once, in Rust (`xian-vm-core`). Today eight rule sets exist twice
(Python + Rust) and must be kept byte-identical by differential tests: fee reservation/refund/failure charge,
contract preparation and entry checks, metadata syscalls, the reward split, stored-value encoding, receipt
assembly, host-write metering, and the static admission fallback. After this work the Python per-transaction path,
the hand-backs and those duplicates are deleted.

## Target architecture
- **Rust owns:** fee path, preparation/entry checks, every syscall (metadata reads and writes, deploy via the
  `xian-compiler-core` crate, random, zk via the `xian-zk` crate), metering, result validation, reward split,
  stored-value encoding, kwargs wire decoding, and the canonical receipt bytes. The hand-back mechanism disappears;
  only a host fault (halt) remains.
- **One engine, two entry points:** `BlockExecutor` for blocks, and `execute_tx(env, overlay, tx, policy, mode)`
  over a forked `BlockState` for single transactions. The simulator, contract-view queries, genesis contract deploys
  and the local `ContractingClient` all use `execute_tx`, so a dry run uses exactly the code a block uses.
- **Python keeps:** ABCI glue, CheckTx/nonce/mempool policy, the decision logic for epoch rebalance and evidence,
  BDS, queries, CLI, genesis and state-patch assembly (bytes encoded by Rust), SDK value types, local test tooling.

## Increments (each one merged and proven before the next)
| # | Step | Size | Consensus | Proof |
|---|------|------|-----------|-------|
| 0 | Parity harness: force-Python switch, golden corpora for deploy/random/zk/owner/system txs/simulation/queries, Python outputs frozen as fixtures | S | no | corpora |
| 1 | Split the Rust block host into modules (metadata, deploy, random, zk) + per-tx host-write layer | S | no | existing differential tests |
| 2 | System transactions (epoch rebalance, evidence penalties) through the Rust executor, unmetered mode | S | no | governance/evidence corpus |
| 3 | `set_owner` / `set_developer` in Rust | S | no | differential |
| 4 | Contract deploy/submission in Rust (compiler crate linked; constructor nested; same error texts) | L | no | differential + bad-source corpus |
| 5 | Random in Rust (same SHA3 stream, same results and errors) | M | no | fuzz against the Python RNG |
| 6 | zk syscalls + proof caches in Rust | M/L | no | shielded corpora, identical chi |
| 7 | Remaining Python-only edge cases get explicit Rust rules (unencodable values, floats, odd balances, uncovered reward inputs) | M | **yes** | "identical except listed cases" |
| 8 | Simulator, queries, genesis deploys, ContractingClient onto `execute_tx`; simulator subprocess/IPC deleted | M | genesis only (hash proven equal) | e2e + estimate == execution |
| 9 | Delete the Python consensus path (`execution_engine`, `process_tx` path, Python reward fallback, `NativeVmHost`, runtime parts of random/zk bridges); stored bytes that `xian.state_root` (rebuild from Python values) and state export/import still write with Python's `encode` go through the Rust writer (`BlockState.write_value`'s conversion) | L | no | golden fixtures, e2e |
| 10 | Retire fallbacks: Python admission path (fastpath-core required); Driver encodes stored bytes via Rust | S each | no | byte-compare fuzz, genesis hash |

Order: 0, 1; then tracks A (2, 3, 4) and B (5) in parallel; then 6 with 10; then 7, 8, 9. At most two Rust tracks
at a time on the laptop; zk last (slow to compile). Every step: determinism campaign, fee/reward corpora, bench;
5-node localnet e2e for 4, 7, 8 and 9.

## Decisions (approved)
1. **Edge cases:** define explicit, documented rules (step 7) in the next unreleased revision, rather than copying
   Python quirks byte-for-byte.
2. **Simulation and fee reservation:** keep today's behaviour: a dry run does not require the sender to hold the
   full `max_tx_chi` budget (200,000 chi), it reports the chi used (otherwise every estimate fails
   for small balances).
3. **Simulator isolation:** run in-process; chi bounds runtime and Rust panics are caught. Drops the subprocess and
   its IPC encoding.
4. **`random.seed` salt:** allow only str/int/None as the extra salt under the new revision, with a clear error
   otherwise (after checking the contracts in xian-contracts/xian-configs); this avoids
   reproducing Python's `str()` for every VM type.
5. **zk in every node build:** yes, one build, no feature variants; costs compile time only.
6. **V1 (old revision-1 contracts):** drop V1 execution from current code; historical V1 replay uses the pinned old
   release (xian-migration already pins abci `8cd5231`). Needs an update of the V1 policy in xian-contracting/AGENTS.md and the xian-meta docs that say
   current code preserves V1 execution (only after confirming xian-migration does not need it).
7. **Transaction decoding:** Rust takes the raw transaction bytes (decode, wire numbers, input hash), removing one
   more Python/Rust duplicate.

## Not ported (and why)
Nonce/CheckTx/mempool policy (node-local), rebalance/evidence decisions (only their transaction runs in the
engine), BDS/queries/CLI (tooling; their bytes go through the Rust encoder), SDK types (display only), CometBFT
events (not consensus), Block-STM (separate, deferred).

## Risks
Compiler error type names reach receipts (must match exactly); local tests that monkeypatch the Python random/zk
bridges or `rt.env` must be rewritten; moving the zk proof cache may change preverify timing (performance only).

## Findings for increment 7 (from the increment-0 corpora, 2026-11-13)
Recorded as golden behaviour today; increment 7 must give each an explicit rule that never halts the chain:
1. A sender balance that is a str, dict, list or bool makes the failure fallback raise in FinalizeBlock (node halt), on both paths.
2. Reward configs with an int validator key or int foundation owner put a non-string key into the receipt; encoding raises in FinalizeBlock (node halt).
3. A malformed reward split (short list, str, dict) fails every paid transaction, including the governance transaction that would repair it.
4. A failed transaction from a sender with a negative balance sets the balance to 0, minting the difference.
5. The Rust "receipt encoding refuses" hand-back (RawDecimal, DecimalTuple, Float, Reference) is unreachable from V2 contracts; remove it with its Python counterpart.
6. Resolved in revision 14 (`fix/random-work-bounds`): `random.seed` salts other than str/int/bool/None and
   `choice`/`choices` populations other than list/tuple/str/bytes/bytearray are defined errors (decision 4),
   checked by the VM before any host. Still handed back: number arguments of other types and call shapes Python
   refuses with its own `TypeError` (wrong arity, unknown keywords); increment 7 gives them explicit errors.
7. The fixed 5-chi base charge is not counted against `chi_supplied` (out-of-chi only when raw cost > supplied x 1000; chi_used = min(raw/1000 + 5, supplied)), so a transaction can supply up to 4 chi less than its cost and still succeed. Approved fix (2026-11-13): the base charge counts against the budget. The simulator must then estimate with the real signed envelope (the sender's real nonce and the final chi value's digits) so exact supply never fails at a chi boundary.
8. Resolved in revision 14 (`fix/random-work-bounds`): host work that grew with an argument is refused or charged
   before it runs, the same on both paths: `getrandbits` above 512 bits fails with the V2 boundary's own text before
   drawing (it used to draw first: k = 2^40 needed 128 GB); `choices` above the sequence limit (131,072) fails like a
   sequence repetition; a range-backed `list`/`tuple`/`set`/`sorted`/`reversed` longer than the limit is refused before
   iterating (it collected 131,072 items for 20 chi first); `importlib.code_hash` charges 4 raw chi per hashed byte
   (a 1 MB IR was hashed on every call for ~6 chi). Checked and already bounded or charged up front: hashlib, crypto,
   zk, string/bytes size arguments, repetition, `bytes(n)`. Python-path only (simulations, contract views until
   increment 8): `shuffle`/`choices` draw at 45-55x the baseline time per chi there (Rust: 4-8x).

9. Found in increment 6 (pre-existing, kept byte-identical on both paths): the zk runtime feature is checked only where
   a module is prepared (the transaction's import graph), by `importlib.has_export` and at deployment. A contract
   that imports a zk contract dynamically (`importlib.import_module`) and calls it still runs its zk syscalls while
   the feature is off. Decided (2026-11-14, as the user intends: with zk off, deployed zk contracts no longer work and
   their transactions just fail): with zk off, every zk syscall fails with an ordinary failed receipt, however the
   contract was reached. Increment 7 implements it (consensus change).

Resolved in increment 6: CI had no zk extra, so the zk parity corpus was skipped in CI. vm-core now links the
verifier, so every corpus runs with the default extras (decision 5).

## Progress

| # | Status | Commits |
|---|--------|---------|
| 0 | done (branch `engine/inc0-parity`, not merged): golden corpora in xian-abci `tests/fixtures/engine_parity/` with `test_engine_parity_corpus.py`; hand-back inventory `handback_inventory.json` (what increments 2-9 move) | xian-abci 2993bca |
| 1 | done (branch `engine/inc1-host-split`, not merged): vm-core `src/block_host/` (BlockHost, metadata reads, IR cache, per-transaction host-write layer `HostWrites` with `NativeVmHost._pending_writes` semantics, not yet staged by any syscall); byte-identical (parity corpora, differential tests, determinism campaign, bench) | xian-contracting d9875fc9 |
| 2 | done (branch `engine/inc2-system-txs`, not merged): epoch rebalance and evidence penalties run in the Rust `BlockExecutor` (`TxProcessor.process_system_tx`; block policy `meter_execution`: unmetered = VM meter off, no failure charge); parity harness captures system receipts at `process_system_tx`, system corpus gains a failing penalty; byte-identical (parity corpora, differential tests incl. a new unmetered one, determinism campaign, bench) | xian-contracting 71daad3f, xian-abci 1a66e6b |
| 3 | done (branch `engine/inc3-owner`, not merged): `contract.set_owner` / `set_developer` in the Rust block host (`block_host::metadata::change` stages via `HostWrites`; `block_host::charges::HostCharges` = `_record_raw_cost`: (encoded key + value) * 25 raw, no write cap, shared budget, entry-contract attribution); only `submission.submit_contract` is still handed back; the executor gets the submission name; byte-identical (owner corpus in Rust with unchanged golden outputs, metadata differential test in paid/free/unmetered mode, determinism campaign, bench) | xian-contracting 7ef32957, xian-abci 1a5fbde |
| 4 | done (branch `engine/inc4-deploy`, not merged): contract submission and `contract.deploy` in the Rust block host (`block_host::deploy`; vm-core links `xian-compiler-core`, whose `compiler_error_message` gives the exact `CompilerError` text; name/exists/source checks, normalize(lint) + IR(lint=false), IR validation, zk check from `__runtime_features.zk` else the node's installed features (`zk_enabled_without_state`), constructor in a nested executor over the same host and budget, metadata + constructor effects staged and charged, `DEPLOYMENT_BASE_COST` + source bytes; missing source fails as `vm_requires_contract_source`); no submission or deploy hand-back left; byte-identical (deploy corpus 41 cases + policy corpora on the Rust path, deployment differential test in paid/free/unmetered mode, determinism campaign, bench). Open: 5-node localnet e2e | xian-contracting a84859f8 14df7743, xian-abci 130cfac |
| 5 | done (branch `engine/inc5-random`, not merged): vm-core `src/block_host/random.rs` (+ `random/stream.rs`): `DeterministicRandom` and the random syscalls in the Rust block host, one state per transaction shared by nested calls (and constructors once deploy runs there); `VmExecutionContext.input_hash` carries the transaction's `__input_hash` from the node. Hand-backs left: finding 6 and the large draws of finding 8. Parity hook `_random_syscalls_debug` fuzzed against the Python bridge; random corpus 35 -> 9 hand-backs (the non-str/int/bool/None salts), `free/random`, `unmetered/random` and `unmetered/out_of_chi` run in Rust too. Also fixed a production-path difference found by the new differential test: the Rust executor charged an entry result with ints of 54-63 bits in its non-V2 encoding (plain number instead of `__big_int__`), so chi and the developer split differed from the Python path; it now runs the bundle in the V2 numeric scope like `execute_bundle`. | xian-contracting 1fc1cbdb 23a0fbb9, xian-abci 5aa6f7e ac0b773 |
| 5b | done (branch `fix/random-work-bounds`, not merged; revision 14): findings 6 and 8 resolved (see above); random corpus hand-backs 9 -> 0; golden changes only for the 9 non-str/int salt cases (README in the fixtures) | xian-contracting 09472e86, xian-abci c546c68 |
| 6 | done (branch `engine/inc6-zk`, not merged): vm-core links the `xian-zk` crate (decision 5; no feature variant). `src/block_host/zk.rs` (+ `zk/checks.rs`, `zk/shielded.rs`) serves all 18 zk syscalls in the Rust block host with the Python bridge's checks and texts (pyo3's `OverflowError` and the helpers' `ValueError` included), registry reads from chain state (block overlay + LMDB, not the transaction's host writes), and verification through `src/zk_cache.rs` (prepared keys 128, verified proofs 2048, process-wide, shared with the Python host); `block_host/features.rs` reads the zk runtime feature for preparation (a zk module with zk off fails as `ContractPreparationError` -> `ValueError`, chi 5, never a halt), `has_export` and deploy. The zk hand-back in `runnable()` is gone (zk corpus 15 -> 0 hand-backs). The Python bridge takes the zk primitives from `xian_vm_core._native` (its LRU caches removed; `shielded_preverify` warms the Rust cache via `zk_warm_registered`); the bridge itself stays for simulations/views until increments 8/9. CI: every parity corpus runs without the zk extra; abci `validate-repo.sh` adds `--extra zk` for the shielded differential test (prover). Proof: zk golden corpus identical on the production path, `benchmark_shielded_chi.py` identical chi on both paths (fixed: it no longer ran), fuzz parity (contracting, 2400 calls) and differential tests (abci) incl. the shielded note flows, determinism campaign, bench (all identical; zk workload 1.46x, shielded transactions 3-20% faster, others unchanged). Open: 5-node localnet e2e | xian-contracting ecf0bb86 89b9c636, xian-abci b6d42e0 cc20381 (on `engine/inc10-admission`), xian-docs-web dc01ba5 |
| 10a | done (branch `engine/inc10-admission`, not merged): one Rust transaction admission. `xian-fastpath-core` is a plain Rust crate (rlib, no Python package any more) linked into `xian-vm-core`, which adds the payload's V2 wire grammar through the stored-value reader (what `_validate_wire_payload` checked in Python) and exposes `decode_and_validate_transaction(raw, chain_id)`; `runtime_info()` reports `tx_admission_revision`. xian-abci requires vm-core, has no `vm`/`native` extras, and the Python static path (`validate_transaction_static`, `check_tx_formatting`, `recurse_rules`, `verify`, `_require_canonical_identity`, `_validate_wire_payload`, ...) is deleted. Proof: admission parity corpus (1649 raw transactions, golden from the old production path) identical through the move; determinism campaign identical; admission throughput +25-35 % (transfer 11-12.6k -> 15-16.5k tx/s, 200-entry kwargs 2-3x). Then, as its own change (approved): admission refuses keys beside `metadata` and `payload` (unsigned keys changed the transaction hash and the block bytes; the Python fallback refused them, the fastpath did not), `xian-fastpath-admission-3`; the corpus diff is exactly the three such cases; genesis fixtures re-hashed. Every other fastpath/Python difference the corpus found was the fastpath being stricter (nesting 125-127, `chi_supplied` 0). | xian-contracting db205109 99bec52b 8a2bb8d0, xian-abci ee472a4 8d1aa04, xian-stack 91714fa 814cdea, xian-ai-skills 8700028, relocks in 11 repos |
| 10b | done (branch `engine/inc10-raw-tx`, on 6 and 10a, not merged; decision 7): the block executor takes raw transaction bytes. `BlockExecutor(..., block_meta=...)` + `add(raw)`; vm-core `transaction_inputs.rs` reads the call, the kwargs (stored-value reader over their canonical JSON = `coerce_call_kwargs(decode_wire_numbers(...))` at the VM boundary), the context (`now` from the block nanos, `__input_hash` = SHA3-256 of nanos + signature) and the canonical size (Python's ASCII escaping) with the admission decoder; Python no longer builds them per transaction (`process_block(txs, raw_txs)`; system transactions encoded by `utils.tx.transaction_bytes`). Proof: input parity over every admitted corpus transaction x 3 block metas + system transactions; engine parity goldens and differential tests unchanged; determinism x32 identical; bench ALL IDENTICAL, 4 reps: transfer200 +12 %, transfer1000 +14 %, DEX +9 %, mix +10 %, random +10 %, scanmeta +17 %, cpu/edge neutral. | xian-contracting 231120dc, xian-abci 93398a7 47b98c8 |
| 10c | done (branch `engine/inc10-driver-encode`, on 10b, not merged): the V2 Driver stages stored bytes written in Rust: `BlockState.write_value(key, value)` / `write_values(items)` (all or nothing) = `py_to_vm` + the aggregate set normalization budget + `encode_stored_value`; `Driver.set` / `apply_writes` use it; `xian_runtime_types.encode` stays for V1 archival data and SDK/BDS JSON. Proof: byte-compare fuzz vs `encode` (600 values of every V2 type, samples, ~40 edges); genesis app hash identical (local 6329ed05..., devnet 966214fe..., built == imported); determinism x32 identical; bench ALL IDENTICAL. Found: the standalone Rust writer missed the aggregate set budget (the VM write path had it), now applied. Refused now, like at the VM boundary (no V2 value; no production caller in the workspace writes one): the standard library's `Decimal` (tests write `ContractingDecimal`), text with a lone surrogate (its key could not be read back) and int subclasses; refusals raise `ValueError` (float was `TypeError`). The remaining Python `encode` users (`xian.state_root`, state export) are listed under increment 9. | xian-contracting 75f955b8, xian-abci 42d7b0d |
| 7-9 | not started | |
