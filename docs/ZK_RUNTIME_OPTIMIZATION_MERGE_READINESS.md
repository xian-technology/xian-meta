# ZK Runtime Optimization Merge Readiness

Status: assessed on 2026-04-09

This note answers one narrow question: which repos in the current shielded
runtime / wallet-sync work can merge now, and in what order?

Scope:

- `xian-contracting` `codex/zk-runtime-optimization`
- `xian-contracts` `codex/zk-runtime-optimization`
- `xian-abci` `codex/zk-runtime-optimization`
- `xian-py` `codex/zk-runtime-optimization`
- `xian-docs-web` `codex/shielded-relay-transfers-docs`
- `xian-stack` `codex/shielded-relay-transfers`

## Recommendation

Merge now:

- `xian-contracting`
- `xian-contracts`
- `xian-abci`
- `xian-py`
- `xian-docs-web`

Merge only in the same coordinated release window, not as an earlier standalone
change:

- `xian-stack`

No separate merge work is needed for:

- `xian-contracting` `codex/shielded-relay-transfers`, because that branch is
  already contained in `codex/zk-runtime-optimization`
- `xian-meta`, because `main` already holds the cross-repo gap tracking and does
  not need a separate topic-branch merge

## Merge Order

1. Merge `xian-contracting`.
2. Merge `xian-contracts` and `xian-abci`.
3. Merge `xian-py`.
4. Merge `xian-docs-web`.
5. Refresh `xian-stack/release-manifest.json` to the merged refs or release
   tags, rerun stack validation, then merge `xian-stack`.

## Why

### `xian-contracting`

- This branch is the foundation for the rest of the runtime work.
- It adds the native shielded bridge helpers now consumed downstream:
  payload-hash builders, shielded public-input builders, relay binding helpers,
  and the prover-service path.
- Downstream branches in `xian-contracts` and `xian-abci` already call these
  APIs directly, so they should not land first.

Validation run:

- `uv run pytest tests/unit/test_zk_stdlib.py -q`
- Result: `17 passed`

### `xian-contracts`

- This branch consumes the new native `zk` stdlib helpers for shielded-note and
  shielded-command flows.
- It also carries the relayed shielded transfer path, which is already part of
  the `xian-contracting` runtime branch ancestry.
- It is merge-ready once `xian-contracting` is in place or lands in the same
  merge window.

Validation run:

- `uv run pytest contracts/shielded-note-token/tests/test_shielded_note_token.py contracts/shielded-commands/tests/test_shielded_commands.py -q`
- Result: `14 passed, 5 deselected`

### `xian-abci`

- This branch depends on the new `xian-contracting` shielded bridge helpers for
  finalize-time preverification.
- It also adds the first selective shielded output-tag indexing and query path,
  which is a meaningful product improvement rather than speculative follow-up
  work.
- There is no independent blocker visible in the code or the targeted tests.

Validation run:

- `uv run pytest tests/abci_methods/test_query.py tests/abci_methods/test_finalize_block.py tests/unit/test_bds_queries.py tests/integration/test_processor.py -q`
- Result: `40 passed`

### `xian-py`

- This branch exposes the new indexed shielded output-tag read surface to apps.
- It should land after `xian-abci`, because its new client surface depends on
  the new `/shielded_output_tags/...` query path.

Validation run:

- `uv run pytest tests/unit/test_xian_clients.py -q`
- Result: `59 passed`

### `xian-docs-web`

- This branch is documentation-only.
- It can merge after the code branches without creating a runtime mismatch.
- It is useful to merge in the same window so the public docs match the shipped
  branch behavior.

### `xian-stack`

- This branch is operationally useful, but it should not merge first.
- It updates `release-manifest.json` to point at exact topic-branch SHAs and
  extends `localnet-e2e.py` for the relayed shielded flow.
- Those manifest refs are not the final merged refs yet, so merging the stack
  branch early would pin the stack to transient topic commits rather than the
  final integration point.
- The right move is to merge the core repos first, refresh the manifest to the
  merged refs or release tags, rerun localnet / release validation, and then
  merge the stack branch.

## Residual Work That Does Not Block These Merges

These branches materially improve the shielded stack, but they do not close the
remaining product and trust gaps by themselves:

- ceremony-grade proving-material import and validation
- canonical network packaging and rotation policy
- threat model and privacy hardening
- network-level disclosure policy
- end-user wallet UX

That follow-up work is real, but it is not a reason to hold back the runtime and
wallet-sync branches from merging.
