# Hybrid account authorization experiment

## Status and boundary

Local experiment, not an accepted transaction format or a network activation.
The implementation lives in
`xian-contracting/packages/xian-accounts/experiments/hybrid-auth/`, outside the
published `xian_accounts` package. No node, SDK, wallet, or validator imports it.

This explores a future extension to [multi-account support](MULTI_ACCOUNT_SUPPORT.md).
That proposal's first version accepts only Ed25519 and Ethereum accounts;
its `xian_tx_v2` envelope does **not** accept this experiment. A production
extension needs its own reviewed format, account registry, migration, and
network-wide activation. [Transaction encoding](TRANSACTION_ENCODING_CONTRACT.md)
remains unchanged.

The subsequent [node registry integration](ACCOUNT_REGISTRY_PROTOCOL.md) uses
separate production framing and preserves existing sender identities. It does
not import or accept the experiment’s account namespace or signatures.

## Security objective

Require both Ed25519 and ML-DSA-65 signatures over the same framed transcript.
There is no single-signature fallback or algorithm negotiation. This is a
candidate defense against future failure of either primitive, subject to review
of the composition and implementations. It does not make the chain quantum
resistant: consensus/light-client authentication, bridges, shielded proofs,
encryption, release signing, and recovery remain separate work.

ML-DSA-65 is specified by [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final).
The experiment uses pure ML-DSA with the empty FIPS context, signing the complete
application transcript; it does not use HashML-DSA or an application prehash.
Application domain separation is in the transcript itself. Ed25519 signs those
same bytes directly.

## Trusted account record

Verification receives a record from trusted state, never keys or policy selected
by the transaction. The record fixes:

- the expected chain identifier (1–64 lowercase ASCII letters, digits, `-`, `_`,
  or `.`, starting with a letter or digit);
- the stable account identifier (`account:` plus 64 lowercase hex characters,
  an experiment-only namespace, independent of either public key);
- a key epoch (unsigned 64-bit integer);
- the Ed25519 public key (32 bytes) and ML-DSA-65 public key (1,952 bytes).

Only the both-required suite exists in this experiment. Ed25519 keys must be
canonical non-identity points in the prime-order subgroup. The signature module
expects already-authenticated state. The separate lifecycle reference model
below authenticates transitions; an optional local SQLite adapter persists them.
Neither model allocates account ids or migrates existing balances/nonces.

Production enrollment must authenticate the existing account and prove
possession of both new keys before classical signatures become forgeable.
Rotation must authenticate the old policy and prove possession of both new
keys, increment the epoch, and atomically invalidate old authorization.
Recovery must preserve equivalent security; an Ed25519-only recovery or
downgrade path would undo the protection. Stable identity also needs an explicit
state/nonce/index migration from existing public-key identifiers.

## Exact experimental byte contract

Integers are unsigned big-endian. `LP16(x)` means a two-byte byte-length followed
by `x`; `LP32(x)` uses a four-byte byte-length. ASCII strings have no normalization.
Fixed strings below are ASCII with a final zero byte where `\0` is shown.

Both primitives sign this transcript, in order:

```text
"XIAN-HYBRID-TX\0"
version:u8 = 1
suite:u8 = 1  # Ed25519 AND ML-DSA-65
LP16(chain_id)
LP16(account_id)
key_epoch:u64
ed25519_public_key:32
ml_dsa_65_public_key:1952
LP32(canonical_payload_bytes)
```

Payloads must be nonempty bytes, at most 131,072 bytes. This is an experimental
resource bound, not a change to current transaction limits. The caller is
responsible for canonical Xian payload serialization and checking its sender,
chain id, nonce, fees, and execution validity. This primitive authenticates bytes;
it is **not** a transaction-admission function. Production adapters must perform
those checks and source the account record from consensus state.

The detached authorization envelope contains exactly:

```text
"XIAN-HYBRID-AUTH\0"
version:u8 = 1
suite:u8 = 1
key_epoch:u64
ed25519_signature:64
ml_dsa_65_signature:3309
```

It contains no public keys, account id, payload, or network-selected policy.
Exact length, domain, version, suite, and current epoch are checked before any
signature work. No trailing bytes, optional fields, missing signatures, or
alternative encodings are accepted. Ed25519 is checked first; ML-DSA is checked
only after it succeeds. This saves work on unauthenticated garbage, but an
attacker with a valid Ed25519 key can still force ML-DSA verification. Production
block/mempool limits and verification metering must budget for that path.

The transcript binds both keys even when testing one component independently.
Changing account, chain, payload, epoch, or either public key invalidates the
authorization. Replay of an identical valid envelope still requires rejection
by the node's nonce/state checks.

## Experimental account lifecycle

`account_lifecycle.py` models one trusted account and three operations. An
initial `LegacyState` contains the chain id, stable experiment account id,
existing Ed25519 public key, and trusted enrollment nonce. That mapping must
come from existing authenticated state; accepting a caller's claimed legacy
key would permit takeover. Account-id allocation/migration is outside this model.

Every enrolled `HybridState` contains two complete `AccountRecord` values:
active keys and separate recovery keys, with the same chain, account id, and
epoch. Both roles always require Ed25519 AND ML-DSA-65. Active/recovery keys
must differ for each primitive. Recovery keys should be kept offline and backed
up separately from active keys; possession of both recovery secrets grants
immediate recovery in this model. There is no timelock or guardian mechanism.
Recovery handles loss of active secrets; it does not prevent theft or replacement
of recovery authority by an attacker who holds both active secrets. The local
request builder holds all supplied secrets in one process for tests; production
wallets need a separate offline recovery-signing and backup workflow.

| Operation | Required current authority | Required new possession proofs | Result |
| --- | --- | --- | --- |
| Enroll (1) | Existing Ed25519 key, while trusted enrollment policy is open | Both new active keys AND both new recovery keys | Hybrid state at epoch 0 |
| Rotate (2) | Both current active keys | Both new active keys AND both new recovery keys | Hybrid state at epoch + 1 |
| Recover (3) | Both current recovery keys | Both new active keys AND both new recovery keys | Hybrid state at epoch + 1 |

Enrollment is permitted only from legacy state. Closing the local enrollment
gate is irreversible for that registry instance and prevents new enrollments;
production must enforce a consensus-controlled cutoff before legacy signatures
become forgeable. The gate cannot retroactively authenticate earlier enrollment.
After enrollment, legacy authorization cannot rotate, recover, or re-enroll.
Every transition replaces all four public keys: neither new role may reuse an
Ed25519 or ML-DSA key from either old role. This retires the current recovery keys on every transition
and prevents carrying a current key over during recovery. Enrollment also
requires replacing the legacy Ed25519 key. Historical keys older than the current
state are not tracked by this model; wallets must generate fresh replacements
and production policy must settle historical-key reuse. Epoch overflow
fails closed. No disable-recovery, return-to-legacy, or single-signature operation
exists. Losing both an active authorization pair and the recovery pair leaves
no supported reset path; backup/recovery UX must make this explicit.

All three proofs authenticate the same operation and complete before/after
state, with distinct role bytes. No application prehash is used. The exact
message signed by each primitive is:

```text
"XIAN-HYBRID-LIFECYCLE\0"
version:u8 = 1
suite:u8 = 1
operation:u8 = 1 | 2 | 3
role:u8 = 1 (current authority) | 2 (new active) | 3 (new recovery)
LP32(encoded_current_state)
LP32(encoded_candidate_state)
```

`encoded_current_state` is either:

```text
legacy: 0:u8 || LP16(chain_id) || LP16(account_id) || enrollment_nonce:u64 || ed_public_key:32
hybrid: 1:u8 || encoded_active_record || encoded_recovery_record
```

The candidate always uses the hybrid encoding. A record is
`LP16(chain_id) || LP16(account_id) || epoch:u64 || ed_public_key:32 || ml_dsa_65_public_key:1952`.
All primitive/string encodings and bounds are as defined above. The role is
signed, so an active possession proof cannot be relabeled as recovery or current
authority. The lifecycle domain is distinct from ordinary transaction signatures.
The existing 3,400-byte hybrid authorization framing carries hybrid proofs;
the legacy authority proof is exactly 64 bytes. Their meaning is determined by
trusted state and explicit operation, never inferred from signature length.

Requests carry the candidate state and the three proofs. The verifier uses its
current trusted state to rebuild every signed message, checks identity/epoch,
key separation/replacement, operation, gate, and all proof lengths before
cryptographic work, then requires all three proofs. Every failure preserves
state. The in-memory registry serializes checking and replacement with a lock;
replayed or concurrent stale requests fail against the newly committed epoch.
The pure transition function alone does not consume state: a production adapter
must atomically compare the trusted state, verify, and commit the replacement,
and retain epochs/nonces across restarts and the chain's state transition rules.

Tests simulate enrollment, rotation, recovery, stale/concurrent requests,
incorrect authority, missing possession, role/operation confusion, substituted
keys, and failure atomicity. This model does not validate an on-chain request
wire format, transaction fees/nonces, consensus persistence, migration cutoff governance,
wallet backup encryption, or compromise-resistant recovery storage.

## Durable local registry and language parity

The optional SQLite registry is a local experiment adapter, not Xian's consensus
state backend. Its database contains public account records and a persistent
one-way enrollment gate, never private keys. Creation is exclusive: opening an
existing database cannot silently reset an account or reopen enrollment. Schema
version, bounded canonical state bytes, and policy types must match exactly;
missing, corrupt, oversized, or unsupported state fails closed.

Each update uses a fresh connection and `BEGIN IMMEDIATE`, reads current state
and policy inside the transaction, verifies the complete request, and commits
its replacement in that same transaction. Failed checks/writes roll back.
Enrollment closure is persisted with the same transaction discipline. SQLite
uses rollback journaling and `synchronous=FULL`; process interruption before
commit must preserve the last committed state. Separate processes contend on
the database lock, rather than relying on a Python thread lock.

This protects ordinary restart/replay and interrupted updates under SQLite's
filesystem assumptions. It does not authenticate database files or prevent a
privileged actor from restoring a valid older database. Production rollback
protection requires the chain's canonical committed state and recovery rules.
The local gate is not a governance-controlled network activation mechanism.

Shared public fixtures exercise transaction transcripts and lifecycle messages,
including malformed encodings, substituted keys, stale epochs, role/operation
confusion, and invalid signatures. Counters use their binary unsigned 64-bit
encoding; JavaScript must use `BigInt`, never lossy JSON numbers. Independent
Python, JavaScript, and Rust reference verifiers consume the same vectors and
reconstruct signing bytes themselves. These are bounded conformance examples,
not a proof of universal acceptance parity or a production library audit.

The binary state decoder consumes exactly the state encoding defined above,
rejects unsupported tags, truncation, trailing data, and oversized inputs before
signature verification, and validates identifiers, key lengths, Ed25519 subgroup membership,
role separation, and matching hybrid identities/epochs. This storage/fixture
codec does not define a live transaction wire format.

## Acceptance gates before integration

- Independent review of the construction, encoding, enrollment, rotation, and
  recovery policy, including substitution and downgrade threats.
- Cross-implementation vectors and adversarial parity across Python, Rust, and
  JavaScript; no acceptance differences among validators.
- Benchmarks of valid and invalid verification, bandwidth, block capacity,
  memory, mobile devices, key storage, and wallet backup/recovery.
- Selection and review of production cryptographic libraries; a local
  experiment with a standardized algorithm is not a validated cryptographic module.
- An explicit extension of the multi-account design and canonical wire
  contract, network policy, authenticated migration rehearsal, and coordinated
  activation plan. No public-network defaults are authorized by this document.
