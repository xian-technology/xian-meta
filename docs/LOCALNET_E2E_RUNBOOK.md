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

# Broad 5-validator whole-stack harness
make localnet-e2e

# VM-native 5-validator harness
make localnet-vm-e2e

# Release-grade validation gate
make release-safety
```

`make localnet-e2e` is the main "test everything" localnet path. It validates
bootstrap, health, `xian-py` smoke, contract orchestration, load, invalid and
conflicting transactions, DEX behavior, simulator load, BDS catch-up, retrieval
APIs, determinism checks, validator governance, state patches, logging,
shielded-note flows, parallel-execution behavior, restart/chaos convergence,
and soak/abuse coverage.

`make release-safety` is the release gate. It combines repo validation,
VM-native e2e, VM rollout reporting, and the focused validator/governance
localnet.

## Source Of Truth

- Public docs: `xian-docs-web/node/localnet-e2e.md`
- Harness implementation: `xian-stack/scripts/localnet-e2e.py`
- Backend wrapper: `xian-stack/scripts/backend.py`
- Make targets: `xian-stack/Makefile`
