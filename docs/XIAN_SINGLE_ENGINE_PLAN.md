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
| 9 | Delete the Python consensus path (`execution_engine`, `process_tx` path, Python reward fallback, `NativeVmHost`, runtime parts of random/zk bridges) | L | no | golden fixtures, e2e |
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
6. Random seed salts other than str/int/None are still handed back to Python after increment 5; decision 4 makes them a defined error.

Also: CI has no zk extra, so the zk parity corpus is skipped in CI; increment 6 (decision 5: zk in every build) must make CI run it.

## Progress

| # | Status | Commits |
|---|--------|---------|
| 0 | done (branch `engine/inc0-parity`, not merged): golden corpora in xian-abci `tests/fixtures/engine_parity/` with `test_engine_parity_corpus.py`; hand-back inventory `handback_inventory.json` (what increments 2-9 move) | xian-abci 2993bca |
| 1 | done (branch `engine/inc1-host-split`, not merged): vm-core `src/block_host/` (BlockHost, metadata reads, IR cache, per-transaction host-write layer `HostWrites` with `NativeVmHost._pending_writes` semantics, not yet staged by any syscall); byte-identical (parity corpora, differential tests, determinism campaign, bench) | xian-contracting d9875fc9 |
| 2-10 | not started | |
