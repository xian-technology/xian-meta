# Account registry and hybrid transactions

## Integration status

This contract defines the node integration under development. It does not
activate a network or certify the cryptographic implementation. Wallet backup
and offline recovery UX, independent review, and deployment rehearsal remain
release gates. The separate hybrid experiment is not the production wire format.

## Identity and compatibility

Keep the existing 64-hex sender string **byte for byte**, including its case.
Do not rewrite balances, allowances, contract owners, nonces, or `ctx.signer`.
Authorization is a separate record at `_accounts.records:<sender>` in consensus
state. This single-underscore namespace cannot be a contract name and is included
in existing state roots and exports. No alias or second account is created.

An absent record means legacy Ed25519 authorization. A present record requires
hybrid authorization; malformed records fail closed. There is no legacy reset
after enrollment. The prior public key remains derivable from an old seed but
no longer grants authority over an enrolled account. New active and separate
recovery credentials must be backed up before enrollment.

Activation is explicit consensus state, never a local preference:
`_accounts.policy = {"version": 1, "enrollment_open": true,
"transition_chi": <positive uint64>}`. Absence disables the new format while
preserving legacy access. Closing enrollment does not disable hybrid spending
or recovery, or freeze unenrolled accounts. A future legacy cutoff requires a
separate reviewed protocol decision. Removing policy while records exist must
not re-enable legacy access. Default genesis bundles explicitly pin enrollment closed.

## Wire contract

Legacy envelopes retain their current encoding. Registry envelopes contain
exactly `payload` and `metadata`. Payload retains the seven existing fields.
Metadata contains exactly `tx_format: "xian_account_v1"` and `auth`.

Ordinary transactions use auth `{scheme: "ed25519_ml_dsa_65_v1", signature}`.
Registry operations use the reserved payload contract `_accounts`, function
`enroll`, `rotate`, or `recover`, and kwargs containing exactly `record`.
Their auth additionally contains `active_proof` and `recovery_proof`. Enrollment
uses scheme `ed25519_enroll_v1`; rotation and recovery use the hybrid scheme.
Recovery keys can authorize only `recover`, never ordinary contract calls.
All signature/public-key hex is lowercase and exact length.

A record contains exactly `version: 1`, `epoch: uint64`, `active`, and `recovery`.
Each role contains exactly `ed25519` (32 bytes) and `ml_dsa_65` (1952 bytes).
Both roles require distinct canonical prime-order Ed25519 keys and distinct PQ
keys. Enrollment starts at epoch zero and replaces the legacy Ed25519 key.
Rotation/recovery increments epoch and replaces both pairs, rejecting reuse of
any current key. Exhausted epochs fail closed.

Every proof binds the complete canonical UTF-8 payload, including chain id,
exact sender, nonce, chi budget, operation, and proposed keys. Hybrid signatures
also bind the signing role's public keys and epoch. Application domains differ
from the prototype and distinguish ordinary, authority, active-possession, and
recovery-possession proofs. Pure ML-DSA-65 uses the empty FIPS context. Both
Ed25519 and ML-DSA-65 must pass; no algorithm negotiation or fallback exists.
Exact framing uses unsigned big-endian integers and no application prehash:

```text
enrollment authority:
  "XIAN-ACCOUNT-ENROLL\0" || 1:u8 || 1:u8 || len(payload):u32 || payload

hybrid message:
  "XIAN-ACCOUNT-TX\0" || 1:u8 || 1:u8 || len(role):u8 || role:ASCII
  || epoch:u64 || ed25519_public:32 || ml_dsa_65_public:1952
  || len(payload):u32 || payload

hybrid signature (3401 bytes):
  "XIAN-ACCOUNT-AUTH\0" || 1:u8 || 1:u8 || epoch:u64
  || ed25519_signature:64 || ml_dsa_65_signature:3309
```

Roles are exactly `transaction` for spending, `authority` for rotation/recovery,
`new_active` for active possession, and `new_recovery` for recovery possession.
Enrollment authority is a 64-byte Ed25519 signature of the enrollment message.
Hybrid authority uses the current active pair for rotation and current recovery
pair for recovery. Possession proofs use the proposed pairs and proposed epoch.
All proofs sign the same canonical payload. The epoch in the signature header
must match the trusted signing record. Strings above use a literal NUL for `\0`.

The implementation is `xian_accounts.hybrid`. Canonical
JSON/ASCII-hex transport follows TRANSACTION_ENCODING_CONTRACT.md. New-format
wire bytes are bounded to 524288 bytes and payloads to 131072 UTF-8 bytes before
cryptographic work. Existing network limits apply before decoding, without
changing the size limit for legacy transactions.

## State transition and ordering

CheckTx reads committed registry state and performs no registry writes.
PrepareProposal, ProcessProposal, and FinalizeBlock use the same authorization
rules and committed nonce sequence. Once a valid registry operation is included,
later transactions from that exact sender are excluded in that block. Earlier
ordinary transactions remain allowed. New keys become usable after Commit.
This barrier also applies when execution later fails for insufficient funds.

Blocks containing registry operations execute serially. Registry operations
perform no VM call. They consume the policy's fixed `transition_chi`, subject
to existing transaction/block budgets, and use existing currency fee accounting.
Insufficient execution-time funds leave authorization unchanged. Successful
registry writes, fees, nonce, app hash, and block marker share the existing LMDB
commit boundary. Snapshots and state exports retain registry records and policy.

Validators with native admission installed use the same state-aware Python
registry path as validators without it. Direct legacy fastpath APIs remain
stateless and cannot authorize registry accounts. SDKs and wallets must query
current state before choosing an envelope; legacy signing remains available for
unenrolled accounts. Installing clients does not activate the node policy.

## Client and release boundaries

The existing `/get/_accounts.records:<sender>` and `/get/_accounts.policy`
queries expose committed public records and policy. Existing `/get_next_nonce/`
semantics are unchanged. Clients must retain the exact sender spelling; display
normalization must not silently change the signed identity.

Current source SDKs and browser/mobile wallets implement hybrid signing and
verified backup/recovery workflows. Enrollment remains explicit and the node
integration is disabled by default. Before distribution, release a
version of `xian-tech-accounts` containing `hybrid.py` and pin that minimum version
in the node release; an already-published account package without this module
cannot run this node revision. Current local development uses the sibling source.
Independent implementation review, production-framing conformance fixtures for
other languages, mobile measurements, and coordinated validator release remain
activation gates; prototype vectors do not certify this wire format.

## Portable backups and wallet custody

The default wallet flow and recommended SDK APIs use the
[single-master backup contract](ACCOUNT_MASTER_BACKUP.md). One fresh master
secret derives distinct active/recovery Ed25519 and ML-DSA seeds with HKDF-SHA-512.
The portable file includes the original address and chain. It requires no second
secret unless the user opts into password encryption. The saved file must be
reopened and match all draft credentials before signing.

Version-2 internal role credentials contain two 32-byte seeds. Older version-1
role files with an expanded 4032-byte ML-DSA private key remain importable. Their
existing AES-256-GCM envelope is unchanged; the master envelope uses a distinct
kind and authenticated domain. The registry and transaction format do not change.
Every rotation/recovery prepares a fresh master and verifies one replacement
backup. Preserve previous/candidate backups until the committed record resolves
the outcome. One current master per account/chain then restores both roles.

Before network I/O, wallets atomically save encrypted candidate active secrets
and the exact signed transaction. Cold recovery secrets are omitted from this
state and from full-wallet backups. A committed record matching a candidate
activates it; CheckTx never does. An archived failed attempt retains its candidate
keys because an earlier broadcast might still commit. Registry read failures,
malformed records or unavailable current keys never trigger legacy fallback.

Full-wallet envelopes containing account vaults use version 3; legacy-only
envelopes remain version 2. A version-2 envelope carrying account vault data is
rejected. Older clients therefore reject genuine version-3 exports instead of
silently omitting hybrid credentials on re-export.

Wallet backup exports include active/pending/retained vault state and explicit
account identity/key pairs inside encryption. Imports validate identity against
the encrypted vault rather than deriving a replacement address. Vault mutations
are serialized; a revision prevents stale settings writes from dropping newer
credentials. Python exposes offline signing/backup primitives; its application
must implement durable persistence and committed-state reconciliation itself.

Current conformance tests compare JS production signatures with the Python
backend and exchange encrypted backups between SDKs. They supplement the node's
balance/allowance/ownership, atomic-commit and recovery tests. They do not replace
independent review or actual Android/iOS device measurements. Registry reads in
these clients trust the configured RPC and are not light-client proofs.

### Custody failure boundaries

Vault implementations serialize read/modify/save workflows, validate saved state
and check read-back before broadcasting. Reuse one `AccountVaultStore` object per
SDK vault; processes or adapters with independent store objects need their own
shared transaction/locking boundary. Atomic individual writes alone do not avoid
lost updates. Wallet adapters cancel work when their session, selected account,
encryption identity or network changes before persistence/broadcast.

Superseded active backups remain encrypted in the retained set because recovered
wallet accounts may use an older seed to bind their local identity. Retention is
not authorization: signing requires a record matching committed registry state.
Backup validation checks private-key signing capability as well as public-key
matching, including cached fields of expanded ML-DSA secrets.

See the [custody review and recovery matrix](../../xian-js/docs/ACCOUNT_CUSTODY_REVIEW.md)
for local fault-injection evidence and remaining enrollment activation gates.
To close enrollment, keep the policy/records and set `enrollment_open` false.
Deleting policy or rolling back to legacy-only validators can strand enrolled
accounts and is not an acceptable emergency disable procedure.


## Multi-validator rehearsal and workspace integration

Enrollment remains disabled in default manifests. The isolated native rehearsal
in `xian-stack/scripts/account-migration-rehearsal.py` runs five equal-power
validators with the release-pinned CometBFT 0.39.3. It uses freshly generated
keys, separate homes and loopback ports; it does not stop or migrate an existing
network. Its durable JSON report records the actual binary version, source
commits, working-tree content hashes, binary hash and Go module identity. The
v0.39.3 source build reports 0.39.0 through its CLI; module build metadata verifies
the actual pinned source version. Private test keys stay in its private
artifact directory, and backup passwords are not retained.

The rehearsal confirms: default policy absence; live JS decoding of absent
registry records; enrollment preserving native/token balances, allowances and
owner identity; rejection of old-key transactions on every validator and a
relayed legacy permit; spending with one crashed validator and catch-up; no
state changes without quorum; recovery after quorum restoration and exact-byte
retry; rejection of obsolete active/recovery keys; full-network crash/restart;
and spending with Python and JavaScript restored from the same encrypted backup.
Sender plus recipient balances are conserved. It uses `free_metered`; configured
fees and failed-transition fee/nonce behavior are covered separately by ABCI
regression tests. This is not a partition/Byzantine or production-volume soak.

CometBFT may gossip a pending transaction back before a retry. A duplicate cache
response is not a failure or a success receipt: reconcile committed record/epoch
and transaction outcome before replacing keys or preparing another transition.
Never restore an old database snapshot as a custody rollback on a live chain.

### Cross-repository integration inventory

| Owning repositories | Account-authentication integration / boundary |
| --- | --- |
| `xian-contracting` account package, `xian-abci` | Hybrid verification, native registry, atomic persistence, commit/proposal validation. Generic VM Ed25519 verification remains a cryptographic primitive, not account authorization. |
| `xian-configs`, `xian-contracts` | Default enrollment disabled. Fresh-chain currency permits and stream relays are removed. Direct calls use the authenticated caller; no legacy permissions are imported. |
| `xian-js`, browser/mobile wallets | Hybrid signer hook, durable vault, verified active/recovery files, committed-state reconciliation, restoration of original identity. |
| `xian-py` | Portable backups/signing and explicit `load_signing_wallet`; recovery material cannot be used as an ordinary signer. Applications own durable transition coordination. |
| `xian-cli` | Transaction commands load encrypted active files; mixed credentials and chain mismatches fail closed. |
| `xian-bridge` | Main and deposit Xian custody can load active backups with original-address checks. Workers must pause/reconcile/restart around rotation. Solana custody is a separate protocol. |
| `xian-dex-automation` | Active-file config, keeper identity validation, admin status and prevention of accidental legacy-key replacement. |
| `xian-mcp-server` | Explicit local configured signer for transactions/tokens/DEX; generic crypto tools remain Ed25519. No recovery secrets in tool arguments. |
| `xian-tg-bot` | Per-original-address encrypted active files; SQLite identity/user association retained, invalid present backups fail closed. |
| `xian-stack` | Isolated rehearsal, hash-pinned ML-DSA backend/image probe, DEX deployer and shielded-relayer outer transaction signing. Generated local test/validator keys deliberately retain existing setup protocols. |
| `xian-nft`, `xian-stable-protocol` | Bootstrap accepts active backups; contract owner strings remain unchanged. |
| `xian-governance-web`, `xian-dex`, `xian-nft`, `xian-ide-web` | Provider/web-kit transaction delegation preserves the full signed envelope and current signer. No application-side replacement cryptography. |
| `xian-contracting-hub-web`, `xian-playground-web` | Hub password/cookie authentication and local VM playground have no production account transaction signer to migrate. |
| `xian-deploy` | Release orchestration consumes coordinated packages/images; no enrollment defaults enabled. Published package names/versions alone do not establish that hybrid code is present. |
| `xian-docs-web`, `xian-ai-guides`, `xian-ai-skills` | Backup/recovery, service configuration, permit boundaries and activation guidance. |
| `xian-linter`, `xian-technology-web`, `xian-xips`, `xian-meta` | Compiler/content/specification or coordination surfaces; no custody signer replacement. Standards/history remain distinct from the implemented account wire format. |
| `xian-intentkit` | Exempt fork, unchanged. Its legacy x402 permit path is not a hybrid account workflow. |

### Contract signatures and remaining activation gates

Enrollment changes transaction authority; it does not revoke arbitrary
signature-based permissions in third-party contracts. The fresh-chain currency
and stream packages expose direct authenticated calls; permit gateways are
removed. Users call `approve`/`create_stream` with the current transaction keys.
New-chain allowances intentionally remain valid across recovery and should be
reviewed separately; old-chain allowances do not enter genesis.
`crypto.verify` is plain Ed25519 verification. Before activation, audit every
selected and subsequently deployed contract for old-key authorization bypasses.
Historical deployments are not patched by editing source files.

Remaining gates: independent protocol/implementation review; browser service-worker
and physical Android/iOS termination, storage and file-provider tests; performance
and malformed-input/DoS measurements on supported devices and release validators;
coordinated versioned package/image releases; mixed-version deployment exclusion;
operator recovery/snapshot rollback drills on the exact release configuration;
and deployed contract/custodian readiness. Closing enrollment retains policy and
records with `enrollment_open=false`; do not remove them or downgrade validators.

The [2026-10-12 security/resource review](../../xian-abci/docs/ACCOUNT_SECURITY_REVIEW.md)
adds local malformed-input/CPU/allocation measurements, an ABCI rejection burst,
SDK depth/KDF guards, archived-candidate downgrade protection and browser/mobile
session lock-race tests. These are local evidence, not release-validator capacity
or physical-device certification. Enrollment remains disabled and final genesis
remains deferred.

Validator consensus, genesis/snapshot signing, Solana, generic login/x402 messages
and shielded proof systems retain separate cryptographic designs. This does not
establish whole-chain quantum security.


### Registry query wire encoding

An absent `_accounts.*` value is encoded as the single zero byte (`AA==` in
CometBFT JSON). Clients distinguish this explicit absence from a missing/null
RPC field or malformed JSON. The latter must stop custody operations rather
than silently selecting legacy authority. Other state-query encodings are
unchanged.

The [deployed-contract upgrade plan](../../xian-stack/docs/DEPLOYED_CONTRACT_UPGRADE_PLAN.md)
records a complete five-validator localnet inventory and source/IR parity for
24 contracts. The isolated source-patch rehearsal preserves all 451 original
state entries except the four intended code artifacts, and rejects old permits
before and after restart. It does not apply a live patch or authorize enrollment.
Persistent allowances, NFT listings/operators and service/governance roles need
explicit custody review. New third-party code and governed upgrades require a
fresh authorization review; snapshot safety is not a permanent chain guarantee.

## Fresh-chain balance import

The accepted launch uses fresh contracts and native-balance migration; the
in-place upgrade evidence above is historical. See
[the migration specification](SNAPSHOT_GENESIS_MIGRATION.md). Production allocation
remains empty/pending, while the importer preserves original account addresses
and pre-enrollment private-key access. The built-in policy is explicitly closed.
No permits, allowances, old streams or registry records enter through the importer.
Legacy x402 settlement is retired from the fresh-chain deployment and e2e paths.
