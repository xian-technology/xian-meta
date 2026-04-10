# Shielded Wallet Recovery Model

Status: current branch-state note after the `zk-runtime-optimization` work

This note explains the current recovery and availability model for Xian's
shielded wallet flows. It is intentionally operational, not aspirational.

The important split is:

- zk correctness and on-chain verification do not depend on BDS
- shielded wallet recovery and note rediscovery do depend on indexed history or
  an equivalent recovery feed

That is normal for privacy systems, but it creates real operational
requirements.

## What Exists Now

Current branches now have all of the following:

- `ShieldedWallet.to_json()` / `from_json()` as the canonical rich wallet
  `state_snapshot`
- browser and mobile wallet flows that can store shielded snapshots, include
  them in encrypted wallet backups, export them directly, and remove them
- browser and mobile wallet checks that can ask the indexed history feed
  whether newer notes exist after a stored snapshot
- a first protocol-shaped `shielded_wallet_history` feed in `xian-abci`
- typed `xian-py` support for that feed
- `xian-zk` wallet sync that prefers the higher-level history feed and falls
  back to older indexed event/tag/transaction reads when needed
- standardized `xian-stack` BDS snapshot export/import commands for operator
  recovery

So the current stack is no longer just "BDS is practical today." It now has a
real first wallet-facing history interface and real wallet-side rich-backup
support.

## What Recovery Actually Means

For a shielded wallet, "recovery" means more than knowing a seed phrase.

A usable restore needs to rediscover:

- which note commitments exist in the pool
- which encrypted payloads belong to the wallet
- which discovered notes are already spent
- enough local commitment history to continue scanning and planning

That is why `seed_backup` and `state_snapshot` are not interchangeable:

- `seed_backup` is the minimal long-term secret
- `state_snapshot` is the richer resume artifact that preserves synced wallet
  state

If you only keep the seed, the wallet still needs indexed historical data to
rebuild its note view.

## Failure And Recovery Cases

### 1. BDS goes down temporarily, history is still available

This is recoverable.

Normal paths:

- BDS catch-up from retained local or remote RPC history
- BDS snapshot import from another indexed node
- wallet restore from a saved `state_snapshot`

### 2. All BDS nodes are lost, but an archival source still exists

This is also recoverable.

You can rebuild the indexed history from:

- an archival CometBFT RPC source
- a previously exported BDS snapshot

### 3. All BDS nodes are lost and historical chain data is pruned away

This is the real danger case.

If there is:

- no surviving BDS snapshot
- no archival RPC source
- no retained local history for reindex
- and the user only has a seed backup but no `state_snapshot`

then older shielded notes may become undiscoverable in practice.

That does not break consensus or proof verification. It breaks wallet
availability and recoverability.

## Operational Requirement

For any network or service that expects shielded wallets to remain recoverable,
all of the following should be treated as required, not optional:

1. at least one indexed node that exports BDS snapshots regularly
2. at least one archival recovery source, or another node capable of exporting
   a full BDS snapshot
3. explicit operator validation of BDS snapshot import/recovery
4. first-class wallet UX for exporting and restoring `state_snapshot` backups
5. first-class wallet UX for checking whether a stored snapshot is already
   stale relative to indexed history

The first two protect the network/service side.

The fourth protects the user side.

Both are needed.

## Current Recommended Posture

Today the pragmatic posture should be:

- keep BDS enabled on the nodes used for wallet-facing indexed reads
- standardize BDS snapshot export/import through `xian-stack`
- treat shielded `state_snapshot` backups as a first-class wallet feature
- keep `seed_backup` as the long-term recovery secret, but do not pretend it is
  the whole restore story
- continue evolving the protocol-shaped `shielded_wallet_history` feed so
  wallet sync does not depend on ad hoc indexed polling forever

## Still Missing

This work improves the system materially, but it does not finish the shielded
product story.

Still missing:

- ceremony-grade proving-material flow
- stronger prover trust boundaries
- network-origin privacy
- richer end-user wallet history and note-status UX
- longer-term protocol/version commitments around wallet history feeds
