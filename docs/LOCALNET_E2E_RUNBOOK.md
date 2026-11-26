# Localnet E2E Runbook

This note records the current cross-repo validation shape for local multi-node
networks. The detailed operator-facing documentation lives in
`xian-docs-web/node/localnet-e2e.md`; this file exists so `xian-meta` does not
keep an outdated 4-node runbook.

## Current Validation Flows

From `xian-stack`:

```bash
# Clean 5-node local network
LOCALNET_NODES=5 make localnet-init
make localnet-up

# Core five-validator chain suite
make localnet-e2e

# Full five-validator whole-stack harness
make localnet-e2e LOCALNET_E2E_SUITE=full

# Release-grade validation gate
make release-safety
```

`make localnet-e2e` checks chain health and agreement, signed payments and
contract rollback, BDS recovery, governed fees, block ordering, crash and
quorum recovery, observer catch-up, and pending nonces. Select the `dex`,
`x402`, or `load` suite for those workflows. The `full` suite adds exhaustive
contract and accounting cases, deeper governance, shielded flows, state
patches, snapshot restore, resource limits, and replay.

`make release-safety` is the release gate. It combines repo validation,
the full e2e, node reporting, and the focused protocol-safety localnet
(`make localnet-protocol-safety`).

## Source Of Truth

- Public docs: `xian-docs-web/node/localnet-e2e.md`
- Harness implementation: `xian-stack/scripts/localnet-e2e.py`
- Backend wrapper: `xian-stack/scripts/backend.py`
- Make targets: `xian-stack/Makefile`
