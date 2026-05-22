# Shielded Relayer Operator Runbook

Status: baseline runbook for the current stack-managed relayer on 2026-04-10

This document is the operator-facing companion to
`PRIVATE_SUBMISSION_RELAYER_ARCHITECTURE.md`.

It describes how to run the current `xian-shielded-relayer` safely enough for
real shared-network use without overstating what the service does.

## Scope

This runbook covers the current `xian-stack` relayer implementation:

- bearer-token auth
- public-route policy
- in-memory rate limiting
- short-lived relayer job retention
- Prometheus-style metrics
- network-manifest publication for one or more relayers

It does not describe a relay mesh, anonymous broadcast network, or split-trust
submission system. The current relayer is still a trusted submission hop.

## Recommended Deployment Posture

### 1. Local development

Use loopback bind and no auth only for local operator or wallet testing.

Recommended posture:

- bind to `127.0.0.1`
- keep `auth_scheme = none`
- keep metrics local
- use permissive allowlists only on isolated environments

### 2. Shared internal environment

Use bearer auth even if the service is only reachable inside a private network.

Recommended posture:

- non-loopback bind with bearer auth
- public `GET /v1/info`
- private quote, submit, job lookup, and metrics endpoints
- conservative job-retention TTL
- request logging enabled without body logging

### 3. Public shared relayer

Treat this as a privacy-sensitive operator service, not as a generic public
API.

Minimum posture:

- bearer auth required
- request rate limits enabled
- metrics not public
- public info only if you actually want discovery probes
- strict allowlists for contracts and targets
- short retention for relayer job history

## Baseline Environment

Example baseline operator configuration:

```bash
export XIAN_SHIELDED_RELAYER_PRIVATE_KEY=<relayer-ed25519-private-key>
export XIAN_SHIELDED_RELAYER_AUTH_TOKEN=<random-bearer-token>
export XIAN_SHIELDED_RELAYER_PUBLIC_INFO=1
export XIAN_SHIELDED_RELAYER_PUBLIC_QUOTE=0
export XIAN_SHIELDED_RELAYER_PUBLIC_JOB_LOOKUP=0
export XIAN_SHIELDED_RELAYER_METRICS_ENABLED=1
export XIAN_SHIELDED_RELAYER_METRICS_PUBLIC=0
export XIAN_SHIELDED_RELAYER_RATE_LIMIT_REQUESTS_PER_MINUTE=120
export XIAN_SHIELDED_RELAYER_RATE_LIMIT_BURST=30
export XIAN_SHIELDED_RELAYER_RATE_LIMIT_TRUST_PROXY=0
export XIAN_SHIELDED_RELAYER_JOB_HISTORY_LIMIT=256
export XIAN_SHIELDED_RELAYER_JOB_HISTORY_TTL_SECONDS=86400
export XIAN_SHIELDED_RELAYER_LOG_REQUESTS=1
```

Start the service through `xian-stack`:

```bash
python3 ./scripts/backend.py start --no-bds-enabled --shielded-relayer
python3 ./scripts/backend.py endpoints --no-bds-enabled --shielded-relayer
python3 ./scripts/backend.py status --no-bds-enabled --shielded-relayer
```

## Auth And Request Policy

Current behavior:

- `/health` is always public
- `/v1/info` can be public or private
- `/v1/quote` can be public or private
- `GET /v1/jobs/{job_id}` can be public or private
- submission routes are private unless auth is disabled entirely
- non-loopback binds require a bearer token

Recommended production posture:

- keep `/health` public
- keep `/v1/info` public only if you want operator discovery
- keep quote private unless you explicitly want pre-auth policy discovery
- keep job lookup private
- keep metrics private

## Rate Limits

The current relayer supports in-memory per-client rate limits.

Relevant settings:

- `XIAN_SHIELDED_RELAYER_RATE_LIMIT_REQUESTS_PER_MINUTE`
- `XIAN_SHIELDED_RELAYER_RATE_LIMIT_BURST`
- `XIAN_SHIELDED_RELAYER_RATE_LIMIT_TRUST_PROXY`

Current behavior:

- limits apply to quote and job routes
- health, info, and metrics are not rate-limited
- client identity comes from the direct remote address by default
- `XIAN_SHIELDED_RELAYER_RATE_LIMIT_TRUST_PROXY=1` tells the relayer to use
  `X-Forwarded-For`

Only enable `TRUST_PROXY` behind a proxy you control.

## Logging And Retention

The current relayer intentionally avoids request-body logging. Keep it that way.

Recommended logging rules:

- log method, route, status, and duration only
- do not log request bodies
- do not log proofs, nullifiers, commitments, payload blobs, or decrypted note
  data
- avoid logging raw client IPs unless there is an explicit operational need and
  a retention policy for them

Retention rules:

- relayer jobs are short-lived operational records, not a privacy archive
- use `XIAN_SHIELDED_RELAYER_JOB_HISTORY_TTL_SECONDS` to keep job lookup
  history bounded
- keep `JOB_HISTORY_LIMIT` bounded even when TTL is long
- rotate or prune service logs on the host according to your operator posture

## Metrics

The relayer exposes a Prometheus-style metrics endpoint at `/metrics`.

Current metric families include:

- `xian_shielded_relayer_requests_total`
- `xian_shielded_relayer_request_duration_seconds_*`
- `xian_shielded_relayer_auth_failures_total`
- `xian_shielded_relayer_rate_limited_total`
- `xian_shielded_relayer_job_history_size`
- `xian_shielded_relayer_current_jobs`
- `xian_shielded_relayer_job_outcomes_total`

Recommended checks:

- request volume and latency
- auth-failure spikes
- rate-limit spikes
- failed job outcomes
- job-history size drifting unexpectedly upward

## Network Manifest Publication

Networks can now advertise more than one relayer with `shielded_relayers`.

Example:

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
    },
    {
      "id": "secondary-us",
      "base_url": "https://relayer-us.example.org",
      "auth_scheme": "bearer",
      "public_info": true,
      "public_quote": false,
      "public_job_lookup": false,
      "priority": 20,
      "submission_kinds": [
        "shielded_note_relay_transfer",
        "shielded_command"
      ]
    }
  ]
}
```

Current CLI selection behavior is intentionally simple:

- sort by `priority`
- break ties by `id`, then `base_url`
- expose the first entry as the primary relayer
- expose the full relayer catalog alongside the primary endpoints

That is good enough for discovery. It is not yet a mesh, quorum, failover, or
trust-reduction protocol.

## Rotation And Incident Response

If a relayer token is exposed:

1. generate a new token
2. restart the relayer with the new token
3. update any clients or proxies that depend on it
4. review request logs and metrics for abuse during the affected window

If the relayer private key is exposed:

1. stop the relayer
2. rotate the relayer account
3. publish updated relayer metadata in the network manifest if needed
4. treat prior quotes as stale and reissue fresh ones from the new relayer

## What Is Still Missing

This runbook improves the current relayer materially, but it does not finish
the network-origin privacy story.

Still missing:

- multi-relayer submission policy beyond simple discovery ordering
- token distribution and client auth lifecycle policy
- shared production guidance for reverse proxies, TLS termination, and regional
  deployment
- a real relay mesh or anonymity-network design
