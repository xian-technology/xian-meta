# Xian Security Audit Follow-Ups

Status as of 2026-06-11:

- fixed: contract metadata privilege escalation
- fixed: remote snapshot bootstrap now supports signed manifest validation
- fixed: secret-bearing MCP tools are disabled by default unless explicitly enabled
- fixed: dashboard SSRF trust boundary (RPC proxy targets constrained to the
  configured node plus currently connected peers)
- addressed: public transaction simulation DoS surface (loopback-default
  bindings with explicit `--public-rpc` opt-in, plus bounded simulation
  workers, timeouts, and chi caps; public-RPC operators accept the residual
  bounded-compute exposure)
- fixed: shielded MiMC hash was non-binding (critical) — replaced with
  Poseidon-BN254 across circuits, contracts, and tooling (`shielded-*-v4`,
  `shielded-command-*-v5`), and nodes on zk-enabled chains require the native
  verifier at startup
- fixed: bridge admin rate-limit bypass via `X-Forwarded-For` — forwarded
  headers are only honored for explicitly configured trusted proxy hops
- fixed: bridge double-mint race — destination transfers run through the
  lease-based durable runtime queue with per-direction idempotency keys

## Fixed Findings

### Contract Metadata Privilege Escalation

`Contract.set_owner(...)` and `Contract.set_developer(...)` are now restricted
to the privileged `submission` path instead of being callable from arbitrary
contracts.

Why this was necessary:

- checking only `ctx.caller == owner` was not sufficient
- a hostile contract executes with the external signer as caller in the Python
  contract runtime
- that let an attacker contract mutate metadata whenever the real owner called
  into it

The trust boundary is now:

- host/admin code can still mutate metadata
- the `submission` contract can still mutate metadata
- ordinary contracts cannot

### Snapshot Bootstrap Provenance

Remote snapshot restore now requires one of:

- explicit `expected_sha256`, or
- a signed snapshot manifest plus trusted signing keys

Signed manifest fields:

- `manifest_version`
- `chain_id`
- `height`
- `snapshot_url`
- `snapshot_sha256`
- `signing_public_key`
- `signature`

The signature is verified against a configured trusted key list, not just a key
embedded in the manifest.

### MCP Secret-Bearing Tools

Unsafe wallet/signing tools in `xian-mcp-server` are now disabled by default.

They require:

- `XIAN_MCP_ENABLE_UNSAFE_WALLET_TOOLS=1`

This gate covers the tools that either return secrets or consume raw private
keys to sign, encrypt, decrypt, or submit transactions.

## Resolved Findings (Implemented Decisions)

### 1. Dashboard SSRF via Peer-Advertised RPC Targets

Implemented model (decision option 2, constrained discovery):

- the dashboard's `rpc` query parameter only proxies to an allowlist built
  from the configured node RPC plus the RPC endpoints of currently connected
  peers
- peer-advertised loopback/wildcard hosts are rewritten to the peer's actual
  remote address before allowlisting
- arbitrary URLs are rejected, removing the generic dashboard-host proxy
  pivot while keeping localnet peer switching

### 2. Public `simulate_tx` DoS Surface

Implemented model:

- simulation runs in bounded worker processes with explicit
  `simulation_max_concurrency`, `simulation_timeout_ms`, and
  `simulation_max_chi` limits
- node bindings are fail-closed loopback by default; exposing RPC (and with
  it simulation) requires the explicit `--public-rpc` opt-in
- operators who deliberately expose public RPC accept the residual bounded
  compute budget; rate limiting at the reverse proxy stays the recommended
  hardening for that posture

## Next Security Pass

For any new pass, rerun:

- targeted unit tests for the touched trust-boundary paths
- a focused source audit around new trust boundaries
- local operator-path validation for dashboard and simulation settings
