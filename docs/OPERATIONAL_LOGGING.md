# Operational Logging Contract

Xian-owned services use logs to explain operational outcomes without changing
transaction results or exposing secrets. Libraries return errors to their caller;
service boundaries own logging and retention. CLI JSON and MCP stdout remain
machine protocols, not log destinations.

## Records

Human-readable records use UTC timestamps with milliseconds and an explicit `Z`,
an uppercase severity, a service/component, a concise message, and named context:

```text
2026-11-03T12:34:56.789Z | ERROR | service/component | Operation failed | stage=submit tx_hash=... error_type=TimeoutError
```

Escape embedded line breaks and control characters and bound external text.
Preserve the same context in structured JSON when that service supports JSON.
Third-party services retain their native formats; container metadata identifies
their source and timestamp. Do not rewrite consensus-engine output to pretend it
uses the application schema.

Include the identifiers needed to follow one operation where available:

- node/service identity and process identity;
- stage or operation, block height/hash and transaction hash/index;
- request, rule, job or incident ID for off-chain operations;
- outcome, exception type and safe reason, retry attempt and next action;
- useful elapsed time or counts for completed batches and recovery operations.

Unexpected failures retain stack locations without captured locals. Expected
rejections use a short reason and correlation fields. Never dump signing keys,
mnemonics, authorization headers, credential-bearing URLs, raw signed requests,
SQL bind parameters, user/chat session dictionaries, contract arguments or full
transaction/state payloads. Prefer static reason codes and safe numeric/status
fields over arbitrary upstream response text.

## Volume and Performance

INFO records startup configuration without secrets, lifecycle transitions,
batch/block summaries and recovery outcomes. DEBUG/TRACE are temporary targeted
diagnostics; disabled diagnostics must not serialize payloads or compute expensive
summaries. Routine successful reads and health probes do not need INFO records.
Repeated failures should retain counters and recovery transitions without flooding
the log. Log maintenance runs outside transaction execution and never contributes
to deterministic state, metering or receipts.

Logging must not introduce unbounded queues or retention scans on every hot-path
record. Cap individual records. Test concurrent writers and orderly shutdown when
a sink or supervisor owns multiple processes.

## Retention Ownership

The default application-file policy is up to seven days with a 250 MiB aggregate
budget per managed log root and a 50 MiB segment limit. Size limits may discard
old entries sooner. Rotate by time as well as size and perform periodic cleanup
when a service is quiet, in addition to startup/rotation cleanup. Document the
cleanup interval and any bounded active-segment allowance. Delete only files
owned by the sink and coordinate concurrent writers before deleting a segment.

Docker owns container stdout/stderr copies. Use its `local` logging driver with
50 MiB segments and five retained segments per container. This is a size/count
bound, not a seven-day age guarantee. Existing containers need recreation to
adopt changed logging settings. Do not truncate or remove Docker-managed files
externally. Do not silently impose a global journald policy on the host.

Host subprocess capture must also be bounded. A rotating application file does
not bound a supervisor's duplicate stdout/stderr file. One-shot test artifacts,
block history, BDS state, backups and operator-exported incident evidence have
separate ownership and retention; log cleanup must not delete them.

## Verification

Exercise safe failure context, timestamp/structure, multiline and oversized input,
secret exclusion, both age and size cleanup, idle cleanup and multi-process
ownership. Verify child-process shutdown and logs after restart for capture
wrappers. Measure representative logging cost and check disabled-debug work.
Keep a log sample and validation evidence without live secrets. Public operator
documentation must state the effective settings, storage paths and limitations.
