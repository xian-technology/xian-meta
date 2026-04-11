# Private Submission Relayer Architecture

## Purpose

Xian already supports proof-bound relayed shielded execution at the circuit and
contract layer. This document defines the next layer above that: the practical
HTTP relayer service a wallet or app can submit to when it does not want to
originate the L1 transaction directly from its own node or RPC path.

This is the current network-layer architecture, not the final privacy end-state.

## Current Components

The implemented cross-repo shape is:

- `xian-contracting` / `xian-contracts`
  proof-bound relayed shielded note transfers and shielded commands
- `xian-py`
  typed Python relayer clients for single-relayer and routed multi-relayer use
- `xian-js`
  typed TypeScript relayer clients for single-relayer and routed multi-relayer
  use
- `xian-stack`
  stack-managed `xian-shielded-relayer` sidecar service
- `xian-configs`
  canonical network manifest fields for single- or multi-relayer discovery
- `xian-cli`
  manifest parsing, relayer catalog ordering, and local sidecar settings

## Service Contract

The relayer is an HTTP service with these endpoints:

- `GET /health`
- `GET /v1/info`
- `GET /metrics`
- `POST /v1/quote`
- `POST /v1/jobs/shielded-note-transfer`
- `POST /v1/jobs/shielded-command`
- `GET /v1/jobs/{job_id}`

`/health` and `/v1/info` are public by default so operator tooling can probe the
service without the submission token. Quote and submission endpoints can be
protected with a bearer token.

The relayer defaults to a loopback bind. If an operator binds it to a
non-loopback host, the current implementation now requires a bearer token.

The current implementation also supports:

- public/private policy for info, quote, job lookup, and metrics
- Prometheus-style metrics at `GET /metrics`
- in-memory per-client rate limits for quote and job routes
- bounded relayer job retention by count and TTL
- request logging that excludes request bodies

## Quote Model

The quote response returns the exact values the proof must bind:

- relayer account
- chain id
- relayer fee
- expiry

This keeps the relayer from changing the fee, swapping in a different relayer
identity, or replaying the proof on another network.

The service does not require quote pre-registration. Quotes are convenience and
policy discovery objects, not capability tokens. Submission still validates:

- minimum fee policy
- allowed note contracts
- allowed shielded-command contracts
- allowed shielded-command targets
- expiry bounds

## Timestamp Rule

`expires_at` uses second-resolution contract time in the canonical string form:

`YYYY-MM-DD HH:MM:SS`

That matters because the proof binds the same logical expiry value the contract
checks on-chain. The relayer converts that string into runtime contract time
before submission.

## Submission Flow

For shielded note relays, the relayer submits:

- contract: the shielded note token contract
- function: `relay_transfer_shielded`

For shielded commands, the relayer submits:

- contract: `con_shielded_commands`
- function: `execute_command`

The relayer uses the normal `xian-py` transaction path, including nonce
reservation, chi estimation, broadcast mode selection, and optional
wait-for-receipt behavior.

Submission responses are stored as relayer jobs with:

- job id
- kind
- status
- contract / function
- tx hash
- submission payload summary
- error, when applicable

The current implementation also supports idempotent `client_request_id`
retries.

Job records are an operational convenience surface, not a privacy archive. They
can include transaction-submission details and should not be exposed broadly or
retained carelessly.

## Stack-Managed Local Runtime

`xian-stack` manages the relayer as an optional sidecar service rather than
embedding it into the node container.

Key runtime controls:

- `--shielded-relayer`
- `--shielded-relayer-host`
- `--shielded-relayer-port`

Key environment variables:

- `XIAN_SHIELDED_RELAYER_PRIVATE_KEY`
- `XIAN_SHIELDED_RELAYER_PRIVATE_KEY_FILE`
- `XIAN_SHIELDED_RELAYER_AUTH_TOKEN`
- `XIAN_SHIELDED_RELAYER_ALLOWED_NOTE_CONTRACTS`
- `XIAN_SHIELDED_RELAYER_ALLOWED_COMMAND_CONTRACTS`
- `XIAN_SHIELDED_RELAYER_ALLOWED_COMMAND_TARGETS`
- `XIAN_SHIELDED_RELAYER_MIN_NOTE_RELAYER_FEE`
- `XIAN_SHIELDED_RELAYER_MIN_COMMAND_RELAYER_FEE`
- `XIAN_SHIELDED_RELAYER_DEFAULT_EXPIRY_SECONDS`
- `XIAN_SHIELDED_RELAYER_MAX_EXPIRY_SECONDS`

This keeps relayer policy outside the node protocol while still making it an
operator-managed part of the stack.

## Minimum Hardening Rules

Operators should treat all of the following as baseline requirements:

- keep the default loopback bind unless there is a real reason to expose the
  service
- if binding on a non-loopback host, set `XIAN_SHIELDED_RELAYER_AUTH_TOKEN`
- keep relayer logs free of request bodies, proofs, and payload blobs
- treat relayer job history as short-lived operational state, not long-term
  storage
- do not market the relayer as an anonymity network or split-trust system

## Network Manifest Discovery

Canonical network manifests can advertise one or more relayers.

Legacy single-entry form:

```json
{
  "shielded_relayer": {
    "base_url": "https://relayer.example.org",
    "auth_scheme": "bearer",
    "public_info": true
  }
}
```

Canonical multi-entry form:

```json
{
  "shielded_relayers": [
    {
      "id": "primary-eu",
      "base_url": "https://relayer-eu.example.org",
      "auth_scheme": "bearer",
      "public_info": true,
      "public_quote": false,
      "public_job_lookup": false,
      "priority": 10,
      "submission_kinds": [
        "shielded_note_relay_transfer",
        "shielded_command"
      ]
    }
  ]
}
```

The CLI currently sorts the catalog by `priority`, then `id`, then `base_url`
and exposes the first entry as the primary relayer while preserving the full
catalog for tooling. The Python and TypeScript SDKs now use that same ordering
for pool clients.

Current routed-client behavior is intentionally asymmetric:

- `getInfo` and `getQuote` can fail over across the ordered relayer catalog
- submission and `getJob` do not auto-fail over once multiple relayers are
  configured
- when more than one candidate relayer exists, submit and job lookup require an
  explicit relayer id so proofs and job ids stay bound to the relayer that owns
  them

That boundary is deliberate. Quote and info are safe to retry on another
relayer. A proof-bound submission or relayer-local job id is not.

These manifest fields are discovery only. They do not distribute secrets,
tokens, or prove that the operator is trustworthy. They tell wallets, tooling,
and operators where the relayer surface lives.

## Trust Boundary

This architecture improves network-origin privacy compared with direct wallet
submission, but it is still not a full anonymous broadcast network.

The relayer learns:

- the IP / transport metadata of the submitter unless another anonymity layer is
  used
- the exact proof, nullifiers, commitments, payload hashes, and relayer fee
- the timing of the submission
- any relayer job metadata it retains locally

The relayer does not need witness secrets if proving is done elsewhere, but it
is still a trusted submission hop.

## What Is Still Missing

The major remaining gaps are:

- client auth lifecycle and token distribution policy
- multi-relayer trust reduction beyond deterministic read-side failover and
  explicit submission routing
- multi-relayer or mesh-style submission instead of single-service trust
- wallet UX that treats relayer selection and failure recovery as first-class
  product flows

So this closes the "run a custom relayer yourself" gap, but it is not yet the
final anonymity network story.
