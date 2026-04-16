# Xian Security Audit Follow-Ups

Status as of 2026-04-16:

- fixed: contract metadata privilege escalation
- fixed: remote snapshot bootstrap now supports signed manifest validation
- fixed: secret-bearing MCP tools are disabled by default unless explicitly enabled
- open: dashboard SSRF trust boundary
- open: unauthenticated public transaction simulation DoS surface

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

## Open Findings

### 1. Dashboard SSRF via Peer-Advertised RPC Targets

Current issue:

- the dashboard accepts peer-advertised RPC addresses
- those addresses become proxy targets
- that lets untrusted network metadata influence where the dashboard host sends
  requests

Current recommendation:

- remove trust in peer-advertised RPC URLs
- allow only static operator-configured RPC targets

Reason:

- this is the clearest trust boundary
- it removes a whole class of dashboard-host pivot risks
- the only tradeoff is losing automatic peer-RPC discovery

Decision options:

1. Static allowlist only
   - strongest fix
   - lowest complexity
   - recommended
2. Keep peer discovery but constrain it to configured host/port patterns
   - preserves more dashboard convenience
   - still leaves a larger attack surface
3. Remove remote RPC proxying and make the dashboard local-node-only
   - strongest reduction in surface
   - bigger product/UX change

### 2. Public `simulate_tx` DoS Surface

Current issue:

- public RPC can expose unauthenticated transaction simulation
- simulation is bounded, but it still gives remote callers a CPU/worker budget

Current recommendation:

- disable public simulation by default
- allow it only on loopback or authenticated operator deployments

Decision options:

1. Default-off except loopback/admin deployments
   - strongest fix
   - recommended
2. Keep remote simulation but require auth
   - acceptable if remote simulation is operationally necessary
3. Keep it public and only tighten limits
   - defense-in-depth only
   - not a complete fix by itself

## Next Security Pass

When the remaining work is resumed, handle it in this order:

1. dashboard RPC target trust boundary
2. public simulation exposure

After that, rerun:

- targeted unit tests for the touched paths
- a focused source audit around the new trust boundaries
- local operator-path validation for dashboard and simulation settings
