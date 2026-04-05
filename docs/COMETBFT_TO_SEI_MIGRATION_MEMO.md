# CometBFT To Sei Migration Memo

## Status

Evaluation memo.

## Scope

This memo evaluates what it would mean for Xian to move from the current
`CometBFT + xian-abci + xian-contracting` architecture to a Sei-style integrated
node stack.

It is not a product decision by itself. It is an architectural input to that
decision.

## Executive Summary

Xian should not switch from CometBFT to `sei-chain` in the near term.

The main reason is structural:

- CometBFT is a generic BFT replication engine with an explicit application
  boundary.
- `sei-chain` is an integrated L1 stack with forked consensus, forked SDK
  layers, forked EVM, custom storage paths, and chain-specific execution
  assumptions.

For Xian, a move from CometBFT to `sei-chain` would not be a drop-in consensus
swap. It would be a re-platforming of the node architecture.

That re-platforming could make sense only if Xian deliberately decides to stop
being a CometBFT-style external application and instead becomes a more
integrated chain binary with much more Go-native execution and storage logic.

Today, that would be a poor fit for Xian's architecture and priorities.

## What Xian Uses Today

Today Xian is explicitly structured around CometBFT:

- `xian-abci` describes itself as the "CometBFT-facing Xian node application"
  and owns ABCI request handling, deterministic chain behavior, and node-side
  services.
- `xian-abci` imports CometBFT ABCI protobuf types directly.
- `xian-stack` starts `cometbft node` directly in the runtime topology.
- Xian docs describe the transaction lifecycle in terms of
  `CheckTx -> consensus -> FinalizeBlock -> Commit`.

This means Xian is not merely "compatible with CometBFT". It is operationally,
test-wise, and conceptually built around the CometBFT application boundary.

Relevant local references:

- `xian-abci/README.md`
- `xian-abci/src/abci/server.py`
- `xian-stack/docker/s6-overlay/etc/xian-services.d/cometbft/run`
- `xian-docs-web/concepts/transaction-lifecycle.md`

## What CometBFT Is

CometBFT is the maintained Tendermint successor and is intentionally focused on
Byzantine Fault Tolerant state machine replication for arbitrary deterministic
applications.

The important architectural property for Xian is not only consensus quality. It
is the explicit separation between:

- the consensus engine and networking layer
- the application process
- the application interface between them

That separation is exactly why Xian can keep its execution model in Python while
letting CometBFT own replication, block production, and finality.

Relevant upstream references:

- https://github.com/cometbft/cometbft
- https://github.com/cometbft/cometbft/blob/main/README.md
- https://github.com/cometbft/cometbft/blob/main/docs/introduction/README.md
- https://docs.cometbft.com/main/

## What Sei-Chain Is

`sei-chain` is not another focused consensus engine. It is a full chain stack.

Its repo structure and dependency graph show that it includes and modifies:

- consensus / Tendermint-style internals
- Cosmos SDK layers
- IBC layers
- storage layers
- EVM integration
- load testing and benchmarking utilities
- optimistic parallel execution infrastructure

Concrete signals:

- top-level directories include `sei-tendermint`, `sei-cosmos`, `sei-db`,
  `sei-ibc-go`, `parallelization`, `giga`, `evmrpc`, `store`, and `x`
- `go.mod` replaces upstream `go-ethereum` with `github.com/sei-protocol/go-ethereum`
- the changelog says `Flatten sei-tendermint go mod into sei-chain`
- the changelog later says `removed tendermint binary and abciclient`
- the changelog also says `Remove ABCI socket/grpc functionality`

That is not "CometBFT plus faster defaults". It is a divergent integrated chain
architecture.

Relevant upstream references:

- https://github.com/sei-protocol/sei-chain
- https://github.com/sei-protocol/sei-chain/blob/main/README.md
- https://github.com/sei-protocol/sei-chain/blob/main/go.mod
- https://github.com/sei-protocol/sei-chain/blob/main/CHANGELOG.md

## The Key Architectural Difference

The real difference is not merely performance.

The difference is where the application boundary lives.

### CometBFT Model

- consensus and networking are generic
- application execution sits outside the engine
- the chain can be written in a different language
- Xian keeps strong ownership of its runtime model

### Sei Model

- consensus, execution, storage, and app layers are integrated tightly
- performance wins come from cross-layer specialization
- the architecture assumes much more of the application stack lives inside the
  node binary and its forked runtime layers

That is why `sei-chain` can achieve optimizations that are hard to get from a
generic engine alone.

It is also why Xian cannot "just switch" to it.

## What Would Have To Change In Xian

If Xian were to move to a Sei-style stack, the following would have to change.

### 1. The External ABCI Boundary Would Stop Being The Main Abstraction

Today Xian is designed around an external application process.

A Sei-style move would force a decision:

- either preserve a compatibility layer while the underlying stack is no longer
  truly organized around it
- or absorb much more of Xian directly into a Go-native integrated node

That means the clean current boundary between CometBFT and `xian-abci` would
become unstable or artificial.

### 2. The Xian Node Topology Would Need A Full Redesign

Current Xian topology assumes:

- `cometbft`
- `xian-abci`
- optional BDS / dashboard / operator services

A Sei-style stack would likely collapse or redefine those boundaries. This would
touch:

- Docker topology
- process supervision
- monitoring jobs
- RPC assumptions
- genesis creation
- state sync and snapshots
- localnet tooling
- node admin and recovery flows

This is a whole-stack change, not a library swap.

### 3. Proposal And Block Handling Would Need To Be Re-Mapped

Xian today maps its behavior onto CometBFT's application lifecycle:

- `CheckTx`
- `PrepareProposal`
- `ProcessProposal`
- `FinalizeBlock`
- `Commit`

Sei has heavily modified application and consensus handling, including internal
ABCI adaptations, consensus extensions, and integrated execution-specific logic.

Xian would have to re-establish:

- nonce semantics
- mempool semantics
- proposal validation semantics
- evidence handling
- finalization semantics
- event indexing assumptions

Any mismatch here is consensus-critical.

### 4. Execution And Storage Assumptions Would Need To Move Closer To The Node

Sei's performance story depends on more than parallel tx scheduling. It also
depends on integrated storage and execution changes such as:

- custom storage paths
- EVM-focused execution optimizations
- chain-integrated parallel processing
- chain-integrated benchmark and replay tooling

For Xian to benefit materially, it would likely have to move more of its own
execution and state machinery into the same integrated node boundary.

That conflicts with the current Xian direction where:

- `xian-contracting` owns execution
- Python remains the authoring and current execution layer
- a future Xian-owned VM is the long-term execution path

### 5. Tooling And Tests Would Need A Major Rewrite

The following Xian surfaces are currently CometBFT-shaped:

- protobuf bindings
- ABCI server wiring
- test fixtures
- localnet orchestration
- dashboard assumptions
- docs and operator workflows
- metrics naming and alerting

The rewrite cost here is real and should not be underestimated.

### 6. The Language / Runtime Mismatch Would Still Exist

Even if Xian moved onto Sei's integrated chain architecture, Xian would still
have its own distinct execution problem:

- Python-authored contracts
- deterministic runtime requirements
- state tracking and metering semantics
- long-term VM ambitions

In other words, a move to Sei would not remove the hardest Xian-specific work.
It would mostly add node-architecture migration work on top.

## What Benefits Xian Might Gain

If Xian did make the switch and carried the re-platforming through successfully,
the likely benefits would be:

- a higher long-term performance ceiling
- access to an integrated performance-oriented chain architecture
- potential gains from lower-latency block handling
- potential gains from more aggressive integrated storage and execution design
- access to ideas already explored in Sei's benchmarking and optimistic
  processing work

These are real benefits.

But they only materialize if Xian adopts much more of Sei's integrated model,
not if it tries to keep the current architecture unchanged.

## What Drawbacks Xian Would Incur

The likely drawbacks are:

- loss of the clean generic consensus/application boundary
- major migration scope across `xian-abci`, `xian-stack`, docs, tooling, and
  tests
- higher operational and maintenance complexity
- tighter coupling to a highly specialized external chain architecture
- more difficult independent reasoning about Xian's own execution semantics
- more difficult long-term path toward a Xian-owned VM

The largest drawback is strategic:

Xian would be adopting another chain's integrated architecture at the exact
layer where Xian most needs clear ownership of its own semantics.

## Why This Would Not Be An Easy TPS Shortcut

It is tempting to think:

- Sei is faster
- therefore switching to Sei should make Xian faster

That reasoning is too shallow.

Sei's performance is not one component. It is a stack property that emerges
from:

- integrated consensus changes
- integrated execution changes
- integrated storage changes
- integrated RPC assumptions
- integrated app-layer choices

Xian would not get those gains cheaply.

And even after a migration, Xian's current contract runtime would still remain a
major bottleneck unless Xian also continues to improve:

- native tx validation
- speculative scheduling
- state backends
- runtime tracing cost
- long-term VM ownership

So the honest answer is:

- switching to Sei might increase the theoretical TPS ceiling
- it would not be an easy or immediate route to higher real TPS for Xian

## Better Path For Xian

The better path is:

1. Keep CometBFT as the consensus engine.
2. Continue improving Xian-owned performance surfaces:
   - tx decode and static validation
   - parallel execution planning
   - conflict handling
   - state backend efficiency
   - query/indexing efficiency
3. Continue the long-term Xian VM path so Python stops being the runtime
   bottleneck while remaining the authoring language.
4. Borrow ideas from Sei where useful without inheriting the whole integrated
   stack.

That means Xian should learn from Sei, not migrate into Sei.

## Borrowable Ideas From Sei Without Switching

Potentially useful themes to study and selectively adopt:

- more aggressive benchmark and replay tooling
- storage-layout work and receipt/query backend ideas
- better write-path batching and async persistence strategies
- better instrumentation of execution phases
- more explicit separation between generic serial-equivalence guarantees and
  performance-oriented optimistic execution paths

These can be imported as ideas and local designs.

They do not require adopting `sei-chain` as the base node runtime.

## Recommendation

Recommendation:

- Do not plan a CometBFT -> Sei-chain migration for Xian.
- Treat Sei as a source of performance ideas, not as the target runtime.
- Keep CometBFT as the consensus foundation unless Xian first decides to become
  a much more integrated Go-native chain with a substantially different node
  architecture.

If Xian ever makes that strategic decision, the migration should be treated as a
new-node-architecture program, not as a consensus-engine upgrade.

## Sources

External:

- `cometbft/cometbft`
- `sei-protocol/sei-chain`
- CometBFT docs and README
- Sei README, `go.mod`, and `CHANGELOG.md`

Local:

- `xian-abci/README.md`
- `xian-abci/src/abci/server.py`
- `xian-stack/docker/s6-overlay/etc/xian-services.d/cometbft/run`
- `xian-docs-web/concepts/transaction-lifecycle.md`
- `xian-meta/docs/XIAN_VM_EXECUTION_MODEL.md`
