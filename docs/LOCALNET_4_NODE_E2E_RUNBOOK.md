# Localnet 4-Node E2E Runbook

This runbook defines the canonical whole-stack local validation path for a
real 4-node Xian network on one machine.

The goal is not a unit-test-style fast loop. The goal is to exercise the live
software stack in a shape that is close to real operator behavior:

- 4 real validators
- real CometBFT networking
- real `xian-abci` processes
- native Rust tracer
- optional BDS/indexed-read path on one service node
- governance-driven validator-set changes
- governance-driven forward state patching
- nested contract deployment and dynamic call routing
- realistic load, conflict, retrieval, logging, DEX, and shielded-token flows

## Why This Exists

The workspace already has many repo-local tests. What was missing was one
repeatable run that validates the integrated behavior of:

- `xian-stack`
- `xian-abci`
- `xian-configs`
- `xian-contracting`
- `xian-contracts`
- `xian-py`
- `xian-zk`

This runbook is the human/operator contract behind the scripted harness in:

- `xian-stack/scripts/localnet-e2e.py`

## Canonical Command

From `xian-stack`:

```bash
make localnet-e2e
```

Equivalent backend entrypoint:

```bash
python3 ./scripts/backend.py localnet-e2e
```

The runner writes machine-readable artifacts under:

```text
xian-stack/.artifacts/localnet-e2e/<run-id>/
```

The top-level result is:

- `summary.json`

Each phase also gets its own JSON file.

## Preconditions

Before running the full exercise:

- Docker is running
- `uv` is installed
- the local workspace contains the core repos side by side
- no conflicting services already use the default localnet host ports
- the host has enough RAM and disk for 4 validators plus a local Postgres
  service node

Recommended local workspace assumptions:

- `xian-stack`
- `xian-abci`
- `xian-configs`
- `xian-contracting`
- `xian-contracts`
- `xian-py`

Optional but recommended for the shielded phase:

- `xian-contracting/packages/xian-zk` is buildable/importable in the local env
- the local validator image also includes `xian-zk`, not just the host-side
  prover utilities

## Important Local-Only Detail

`xian-stack/.localnet/network.json` contains local validator private keys so the
runner can exercise real on-chain validator governance. Those keys are
disposable dev artifacts and must never be reused outside this local network.

## What The Runner Covers

The canonical phase order is intentional. The scenarios build on each other.

### 00 Bootstrap

Creates a fresh 4-node localnet with:

- native Rust tracer
- one BDS-enabled service node
- local validator keys
- deterministic metadata captured in `network.json`

Pass criteria:

- all nodes start
- chain ID and localnet metadata are captured
- the selected tracer is `native_instruction_v1`

### 01 Health

Validates the basic live network:

- `/status`
- `/net_info`
- `/validators`
- recent app-hash equality across nodes
- BDS status on the service node

Pass criteria:

- all nodes are live
- peer counts are healthy
- recent app hashes match

### 02 xian-py Smoke

Uses `xian-py` as the first real client path:

- derive wallets
- fund accounts
- deploy helper contracts
- simulate
- query state
- call exported functions

Pass criteria:

- client submission works
- receipt handling works
- state reads and simulation results are sane

### 03 Contract Orchestration

Exercises cross-contract behavior that is easy to miss in isolated repo tests:

- a contract submits multiple child contracts in one transaction
- child deployment metadata is checked for `__developer__`, `__deployer__`,
  `__initiator__`, and constructor context
- a routed contract dynamically chooses both contract name and function name
- a multi-hop root -> router -> mid -> leaf call chain preserves
  `ctx.caller`, `ctx.signer`, and `ctx.entry`
- a nested child-constructor failure rolls back the whole batch deployment

Pass criteria:

- both factory-deployed children exist after the success path
- child deployment metadata points at the factory contract and original signer
- dynamic routing succeeds for allowed exports
- private or non-exported dynamic calls fail
- the failed batch deployment leaves no child contracts behind

### 04 Periodic Load

Sends low-rate periodic transfers from multiple nodes and multiple senders.

This is the “normal traffic” baseline before burst traffic starts.

Pass criteria:

- all transfers finalize successfully
- the runner captures approximate TPS

### 05 Burst Load

Runs the existing deterministic burst workload against the live localnet.

Pass criteria:

- the burst scenario succeeds
- receipts resolve correctly
- approximate TPS is captured

### 06 Conflict / Invalid

Exercises intentionally conflicting and invalid behavior:

- two transactions race for the same contract slot
- one should win and one should fail
- an invalid claim is submitted deliberately and must fail

Pass criteria:

- exactly one of the conflicting txs succeeds
- invalid txs fail for the right reason class

### 07 DEX Mixed

Deploys and exercises the DEX contract pack with a richer mixed workload.

Pass criteria:

- deployment succeeds
- approvals, liquidity, swaps, and failure cases execute
- DEX contracts become available for later phases

### 08 Simulator Load

Hammer-tests readonly simulation with many concurrent requests against the live
DEX state.

Pass criteria:

- simulations complete within configured limits
- the runner captures approximate simulator QPS
- no silent failure class appears

### 09 BDS Catch-Up

Intentionally forces the indexed path behind live chain execution:

- stop the local Postgres service
- keep submitting real transactions while the chain continues advancing
- verify BDS reports lag, backlog, or spool activity
- restart Postgres
- wait for BDS to catch up to the validator height again
- verify lagged transactions become queryable through the indexed surface

Pass criteria:

- live block production continues while Postgres is down
- BDS shows clear evidence of falling behind
- BDS returns to `indexed_height == current height`
- lagged tx/event/state records are queryable again after recovery

Operational note:

- use indexed height, spool state, and DB health as the real recovery
  indicators. On the current service-node runtime, `queue_depth` can remain
  nonzero in steady state and should not be treated as a hard failure by
  itself.

### 10 Retrieval Surfaces

Validates the main read paths:

- BDS-backed indexed block lookup
- indexed event lookup
- indexed state history lookup
- tx-to-state lookup
- tx-to-events lookup
- watcher flow through `xian-py`
- raw websocket tx subscription

Pass criteria:

- all retrieval surfaces return coherent data
- a newly-triggered event is seen through both indexed and live watch paths

### 11 Determinism

Performs a focused determinism check after meaningful state exists:

- recent app-hash equality
- direct state equality across all validators
- same simulation on every validator produces the same result and stamp usage
- sampled state from the orchestration phase remains identical across validators

Pass criteria:

- all validators agree on sampled state
- all validators agree on recent app hashes
- simulation outputs do not drift by node

### 12 Validator Governance

Exercises real on-chain validator governance with the local validator keys:

- change validator power
- remove a validator
- re-register the removed validator
- vote the validator back in

Pass criteria:

- the validator set shrinks and grows again
- power changes actually propagate
- reward/power metadata stays coherent

### 13 State Patch

Exercises the full governed forward-patch flow:

- identical local bundles are placed on every validator
- governance approves the bundle hash and activation height
- the patch applies at the target block
- indexed patch history is queryable afterward

Pass criteria:

- the patch is approved on-chain
- the bundle hash matches the local bundle
- the patch target contract state changes only at activation
- indexed patch history is present

### 14 Logging

Validates practical operator logging behavior:

- switch to `DEBUG`
- trigger txs and inspect stage logs
- switch to `TRACE`
- trigger txs and inspect deeper trace output
- restore the configured log level

Pass criteria:

- log files rotate under the expected path
- `DEBUG` emits compact tx-stage logs
- `TRACE` emits deeper finalize payload traces

### 15 Shielded Note Token

Exercises the current privacy-stack candidate:

- use the governed system `zk_registry`
- deploy shielded-note-token
- register and bind dev verifying keys
- mint public supply
- deposit into the shielded pool
- shielded transfer
- shielded withdraw back to public balance

Pass criteria:

- all proof-backed steps finalize
- note payload recovery works for intended viewers
- public and shielded supply accounting remains coherent

Operational note:

- this is typically the slowest phase in the full run. Real proving work can
  keep the runner in this phase for several minutes even when the phase is
  succeeding.

Important current boundary:

- the runbook does not currently list the shielded token on the DEX
- the present DEX fixture expects float-based token semantics, while the
  shielded-note-token public interface uses integer amounts
- that integration should be treated as a separate compatibility project, not a
  quick add-on to the canonical whole-stack validation run
- the canonical shielded flow uses explicit transaction stamp ceilings, because
  readonly simulation is intentionally capped below proof-backed shielded
  execution cost
- hex-looking public addresses are valid withdraw recipients, so the toolkit and
  contract must stay aligned on the same recipient-digest hashing semantics

Useful resume command after a partial run:

```bash
python3 ./scripts/backend.py localnet-e2e \
  --start-phase 10-retrieval-surfaces \
  --resume-dir xian-stack/.artifacts/localnet-e2e/<run-id>
```

## Recommended Execution Matrix

The canonical base run is:

```bash
make localnet-e2e
```

After that, the useful repeat matrix is:

### 1. Integrated Topology, Parallel Off

Purpose:

- baseline reference run

Command:

```bash
XIAN_LOCALNET_TOPOLOGY=integrated \
XIAN_LOCALNET_PARALLEL_EXECUTION_ENABLED=0 \
make localnet-e2e
```

### 2. Integrated Topology, Parallel On

Purpose:

- stress speculative execution and fallback behavior

Command:

```bash
XIAN_LOCALNET_TOPOLOGY=integrated \
XIAN_LOCALNET_PARALLEL_EXECUTION_ENABLED=1 \
XIAN_LOCALNET_PARALLEL_EXECUTION_WORKERS=4 \
XIAN_LOCALNET_PARALLEL_EXECUTION_MIN_TRANSACTIONS=4 \
make localnet-e2e
```

### 3. Fidelity Topology, Parallel Off

Purpose:

- closer process separation to production-style orchestration

Command:

```bash
XIAN_LOCALNET_TOPOLOGY=fidelity \
XIAN_LOCALNET_PARALLEL_EXECUTION_ENABLED=0 \
make localnet-e2e
```

### 4. Fidelity Topology, Parallel On

Purpose:

- strongest local integration check

Command:

```bash
XIAN_LOCALNET_TOPOLOGY=fidelity \
XIAN_LOCALNET_PARALLEL_EXECUTION_ENABLED=1 \
XIAN_LOCALNET_PARALLEL_EXECUTION_WORKERS=4 \
XIAN_LOCALNET_PARALLEL_EXECUTION_MIN_TRANSACTIONS=4 \
make localnet-e2e
```

## Useful Overrides

Examples:

```bash
LOCALNET_E2E_BUILD=1 make localnet-e2e
LOCALNET_E2E_BURST_COUNTER_OPS=500 make localnet-e2e
LOCALNET_E2E_DEX_ROUNDS=12 make localnet-e2e
LOCALNET_E2E_BOOTSTRAP=0 make localnet-e2e
```

Use `LOCALNET_E2E_BOOTSTRAP=0` only when the localnet is already up and you
deliberately want to rerun the phased checks against the current network.

## Artifacts To Review After Each Run

Always inspect:

- `summary.json`
- the phase JSON files
- the service-node BDS status in the retrieval/state-patch phases
- log snippets captured by the logging phase

For failures:

- inspect `.localnet/<node>/.cometbft/xian/logs/`
- inspect Docker container logs
- compare the last successful phase to the first failing one

## What This Runbook Does Not Replace

This runbook is for integrated local validation. It does not replace:

- repo-local unit/integration tests
- remote deployment runbooks
- production recovery plans
- governance or incident-response policy

It exists so the stack has one repeatable whole-network validation path that is
close enough to real operator behavior to catch integration bugs early.
