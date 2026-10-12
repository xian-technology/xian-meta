# Single-master account backup contract

Status: implementation and local validation; enrollment remains disabled.

The account registry and transaction authorization stay at version 1. A master
is a fresh 32-byte CSPRNG secret, never the legacy Ed25519 seed. Derivation uses
HKDF-SHA-512, salt `XIAN-ACCOUNT-MASTER\0v1`, 32-byte outputs, and UTF-8 canonical
JSON info `[chain_id, sender, epoch, role, algorithm]`. Roles are `active` and
`recovery`; algorithms are `ed25519` and `ml-dsa-65`. Sender case is preserved.
ML-DSA seeds expand through FIPS 204 key generation. Derivation is versioned and
identical across Python, browser and mobile SDKs.

The portable JSON master backup has exactly `version: 1`,
`kind: "xian-account-master"`, `chain_id`, `sender`, `record`, and `master_seed`.
`record` is the full derived public account record, including epoch. Import
re-derives and compares it before use. It is not proof of activation: restoring
or using recovery authority also requires matching the committed registry on the
bound chain. Public metadata is included so no original identity secret is
needed. The plaintext backup is itself the secret and requires no second backup
password. Optional password encryption uses a distinct authenticated envelope.

Derived role credentials use `xian-account-backup` version 2, with
`secret.ed25519_seed` and `secret.ml_dsa_65` each a 32-byte seed. Version 1 retains
its expanded 4032-byte ML-DSA secret and remains importable. Never interpret a
version-1 expanded key as a seed. Role credentials are internal wallet state,
not separate user backup requirements.

The default wallet transition workflow generates a fresh master for enrollment,
rotation or recovery. Export and reopen one master backup, compare all derived
credentials against the draft, then permit signing. Save the derived active
credentials and exact signed transaction durably before network submission.
Store no master or recovery secrets in the persistent everyday vault or full
wallet/session export. Failed writes stop submission; retries use exact bytes;
uncertain candidate active keys remain retained.

A current master restores active access or supplies recovery authority. Recovery
and rotation replace both pairs with a fresh master and require a newly verified
backup. Keep the previous and candidate backups until commitment is known; after
confirmation one current master backup suffices for this account. This is one
backup per enrolled account/chain, not a wallet-wide seed for unrelated accounts
or shielded notes. Loss/theft of the master cannot be repaired by deriving more
children from that same master. Recovery cannot reverse a completed theft.

Legacy independent active/recovery backups remain accepted in their appropriate
roles. An existing independently generated account can adopt the master model
through an authorized rotation/recovery without changing its address or funds.
No registry or genesis activation is implied by this client-side format.
