# Multi-Account Support Design

## Status

Proposed implementation target.

This document defines the target design for adding multiple transaction-account
schemes to Xian while keeping validator consensus keys unchanged.

It is intended to be precise enough to implement against without inventing
additional semantics during implementation.

## Scope

This design applies to:

- `xian-abci`
- `xian-contracting`
- `xian-py`
- `xian-cli`
- `xian-configs`
- `xian-stack`
- `xian-docs-web`

## Goals

- Allow Xian transactions to be authorized by more than one account scheme.
- Preserve clean and deterministic transaction verification.
- Make Ethereum-wallet compatibility possible for native Xian transactions.
- Keep validator consensus keys and user transaction accounts as separate
  concerns.
- Make one mnemonic able to derive multiple Xian account families cleanly.

## Non-Goals

- Reusing the same raw private-key bytes across Ed25519 and secp256k1.
- Replacing CometBFT validator consensus keys with Ethereum-style keys.
- Supporting every Ethereum signing mode in the first version.
- Supporting ambiguous or non-canonical account identifiers.
- Supporting mixed legacy and typed account identifiers indefinitely.

## Core Decisions

1. Validator consensus keys stay `ed25519`.
2. Transaction accounts support multiple authorization schemes.
3. Xian uses typed account identifiers, not ambiguous bare strings.
4. The same mnemonic may derive multiple account families, but each family keeps
   its own standard derivation and curve semantics.
5. The first Ethereum-compatible transaction scheme is
   `secp256k1_eth_personal_sign_v1`.
6. The first Ed25519 transaction scheme is `ed25519_raw_v1`.
7. Xian does not support a dual identity for the same logical account under both
   legacy and typed forms. Networks must migrate cleanly.

## Terminology

- `consensus key`: the validator key used by CometBFT consensus. This remains
  `ed25519`.
- `transaction account`: the identity used as `payload.sender` for Xian
  transactions.
- `account family`: the identifier family of the transaction account, for
  example `ed25519` or `eth`.
- `auth scheme`: the concrete signing and verification rule used for a
  transaction, for example `ed25519_raw_v1`.
- `account id`: the canonical string stored in state, transactions, BDS, and
  contract context.
- `signable payload`: the canonical payload string that is signed by the chosen
  auth scheme.

## Separation Of Concerns

### Consensus Keys

Consensus keys remain unchanged:

- CometBFT validator keys stay `ed25519`.
- node keys stay `ed25519`.
- validator address derivation remains whatever CometBFT currently uses.

This design does not alter validator consensus identity.

### Transaction Accounts

Transaction accounts become explicitly multi-scheme.

Everything below uses transaction accounts:

- `payload.sender`
- nonce tracking
- balance ownership
- contract `ctx.signer`
- BDS sender indexing
- transaction history queries
- SDK wallets and transaction signing

## Canonical Account Identifier Format

Transaction accounts are stored and transmitted as canonical typed strings.

### General Rules

- Account identifiers are ASCII strings.
- Account identifiers are lowercase only.
- Account identifiers must not contain whitespace.
- Account identifiers must not contain `/`.
- Account identifiers are compared byte-for-byte after validation. There is no
  secondary normalization step during execution.

### Supported Account Families In The First Version

#### Ed25519 Account Id

Format:

```text
ed25519:<64 lowercase hex chars>
```

Regex:

```text
^ed25519:[0-9a-f]{64}$
```

The hex body is the 32-byte Ed25519 public key.

Example:

```text
ed25519:7f4c2a3e6d7c8b2f0a1e9d4c5b6a7980112233445566778899aabbccddeeff00
```

#### Ethereum-Compatible Account Id

Format:

```text
eth:0x<40 lowercase hex chars>
```

Regex:

```text
^eth:0x[0-9a-f]{40}$
```

The hex body is the 20-byte Ethereum address in lowercase canonical form.

Example:

```text
eth:0x23129f307148e121e2d29e52fdb520989d325e37
```

### Canonicalization Rules

- `ed25519` public keys are lowercase hex, no `0x`.
- `eth` addresses are lowercase hex with required `0x`.
- Mixed-case EIP-55 addresses are valid for wallet display, but not as canonical
  on-chain account identifiers.
- SDKs may accept mixed-case Ethereum input from users, but must convert it to
  lowercase canonical form before building and signing the transaction.

### Rejected Formats

These are invalid in the new model:

- bare 64-hex Ed25519 public keys
- bare `0x...` Ethereum addresses without the `eth:` family prefix
- uppercase or mixed-case canonical account ids
- whitespace-padded account ids

## Transaction Envelope

The multi-account transaction envelope is a new format and must be treated as a
new transaction format, not as an implicit extension of the legacy one.

### Canonical Transaction Shape

```json
{
  "metadata": {
    "tx_format": "xian_tx_v2",
    "auth": {
      "scheme": "<auth scheme id>",
      "signature": "<lowercase hex>"
    }
  },
  "payload": {
    "sender": "<canonical account id>",
    "nonce": 1,
    "stamps_supplied": 1000,
    "contract": "currency",
    "function": "transfer",
    "kwargs": {
      "to": "eth:0x...",
      "amount": 1
    },
    "chain_id": "xian-mainnet"
  }
}
```

### Envelope Rules

- `metadata.tx_format` must be exactly `xian_tx_v2`.
- `metadata.auth` must contain exactly:
  - `scheme`
  - `signature`
- `metadata.auth` must not contain `public_key`, `address`, `v`, `r`, `s`, or
  any other auxiliary fields in the first version.
- `payload` keeps the current field set and semantics.
- `payload.sender` must already be canonical.

### Why `tx_format` Is Explicit

The new model should not rely on heuristic inference from field shapes.

An explicit format marker:

- prevents ambiguous parsing
- makes upgrades safer
- gives a clean migration boundary
- avoids future overloading of the legacy envelope

## Auth Schemes

The first implementation supports exactly these auth schemes:

- `ed25519_raw_v1`
- `secp256k1_eth_personal_sign_v1`

### Auth Scheme To Account Family Mapping

The mapping is fixed:

- `ed25519_raw_v1` requires an `ed25519:` sender
- `secp256k1_eth_personal_sign_v1` requires an `eth:` sender

Nodes must reject any transaction where `payload.sender` family and
`metadata.auth.scheme` do not match.

### Generic Signature Encoding Rule

- `metadata.auth.signature` is lowercase hex without `0x`.

Per scheme:

- `ed25519_raw_v1`: exactly 128 hex chars
- `secp256k1_eth_personal_sign_v1`: exactly 130 hex chars

The network must reject malformed lengths before attempting verification.

## Signable Payload Definition

The signable payload remains the canonical encoded Xian transaction payload
projection.

### Signable Payload Projection

The signable projection is exactly:

```json
{
  "chain_id": "<payload.chain_id>",
  "contract": "<payload.contract>",
  "function": "<payload.function>",
  "kwargs": "<payload.kwargs>",
  "nonce": "<payload.nonce>",
  "sender": "<payload.sender>",
  "stamps_supplied": "<payload.stamps_supplied>"
}
```

No other fields are included.

### Canonical Serialization

The signable payload string is:

```text
encode(decode(encode(signable_projection)))
```

using Xian's canonical runtime-type encoding.

This yields a canonical JSON string.

### Signed Byte Source

- The canonical JSON string is encoded as UTF-8.
- All auth schemes in this design sign that canonical message, but they wrap it
  differently according to their scheme rules.

This preserves the current Xian signing basis while allowing additional auth
schemes.

## Verification Algorithms

The verification rules below are normative.

### `ed25519_raw_v1`

#### Preconditions

- `payload.sender` matches `^ed25519:[0-9a-f]{64}$`
- `metadata.auth.signature` matches `^[0-9a-f]{128}$`
- `metadata.auth.scheme == "ed25519_raw_v1"`
- `metadata.tx_format == "xian_tx_v2"`

#### Verification

1. Extract the 64-hex public key body after `ed25519:`.
2. Build the canonical signable payload string.
3. UTF-8 encode the signable payload string.
4. Decode the signature hex into 64 bytes.
5. Verify the Ed25519 signature directly against the message bytes using the
   extracted public key.

#### Acceptance Rule

The transaction is valid only if signature verification succeeds exactly.

### `secp256k1_eth_personal_sign_v1`

#### Preconditions

- `payload.sender` matches `^eth:0x[0-9a-f]{40}$`
- `metadata.auth.signature` matches `^[0-9a-f]{130}$`
- `metadata.auth.scheme == "secp256k1_eth_personal_sign_v1"`
- `metadata.tx_format == "xian_tx_v2"`

#### Verification

1. Extract the lowercase canonical Ethereum address body after `eth:`.
2. Build the canonical signable payload string.
3. Use the canonical signable payload string as UTF-8 text for Ethereum
   `personal_sign` / EIP-191 version `0x45` message signing.
4. The signed message bytes are the UTF-8 bytes of the canonical signable
   payload string.
5. The EIP-191 prefix length is the decimal byte length of those UTF-8 message
   bytes.
6. Recover the signing address from the 65-byte recoverable signature.
7. Lowercase the recovered address and compare it to the lowercase canonical
   sender address body.

#### Equivalent Wallet Semantics

This is equivalent to:

- MetaMask `personal_sign`
- `eth_account.messages.encode_defunct(text=payload_string)`

#### Acceptance Rule

The transaction is valid only if the recovered lowercase address matches the
canonical lowercase sender address exactly.

### Important Security Rules

- The node must not infer the auth scheme from signature length.
- The declared auth scheme is authoritative and must match the sender family.
- `payload.sender` is part of the signed message and must not be reconstructed
  from external metadata.
- `payload.chain_id` remains mandatory in the signable payload and protects
  against cross-chain replay.

## Network Configuration

Account-scheme support must be a network policy, not a local node preference.

### Required Policy Surface

Each network must define:

```yaml
accounts:
  tx_format: xian_tx_v2
  allowed_auth_schemes:
    - ed25519_raw_v1
    - secp256k1_eth_personal_sign_v1
```

Rules:

- Every validator on the network must use the same allowed auth-scheme set.
- A node must refuse startup if its local execution policy does not match the
  network configuration.
- A transaction using a disallowed auth scheme must fail deterministic
  validation.

### Recommended Network Modes

Supported network policies should be:

- Ed25519-only
- Ethereum-compatible-only
- dual-account support

This lets different networks choose their own transaction-account model without
changing consensus keys.

## State, Nonce, And Indexing Implications

### State Ownership

State keys that represent account ownership or balances must use the canonical
account id string.

Examples:

- balances
- allowances
- voting rights
- membership lists
- owner/admin fields

There must be no hidden normalization after state lookup. The stored key is the
canonical account id.

### Nonce Tracking

Nonce tracking keys use the canonical account id string exactly.

This applies to:

- committed nonces
- mempool reservations
- proposal/block nonce validation

### BDS

BDS stores the canonical sender account id as the authoritative sender field.

Optional optimization fields may be added later, for example:

- `sender_family`
- `sender_body`

but they are secondary indexes, not canonical identity fields.

### Query Surface

Query endpoints that accept a sender identifier must accept the canonical
account id string.

Clients should URL-encode the full account id when constructing path-based
queries.

## Contract Runtime Implications

### `ctx.signer`

`ctx.signer` becomes the canonical transaction account id string.

Examples:

- `ed25519:...`
- `eth:0x...`

### `ctx.caller`

`ctx.caller` keeps its current meaning:

- external call root: same canonical transaction account id as the signer
- nested contract call: the immediate calling contract name

This means `ctx.caller` remains a union of:

- canonical account id
- contract name like `con_token`

That distinction already exists today and remains valid.

### Contract Guidance

Contracts must not assume account identifiers are fixed-length hex strings.

The standard contracts and contract docs should move toward helper-based account
validation rather than string-length checks.

Recommended future helpers:

- `account.is_account_id(value)`
- `account.family(value)`
- `account.is_ed25519(value)`
- `account.is_eth(value)`

## Wallet And SDK Implications

### Wallet Model

Wallets must expose:

- `account_family`
- `auth_scheme`
- `account_id`
- display-oriented fields where helpful

The current Ethereum wallet property named `public_key` should be replaced in
the SDK with explicit naming like `address` or `account_id`.

### Mnemonic Strategy

One mnemonic may derive multiple Xian account families:

- Ed25519 account
- Ethereum-compatible secp256k1 account

This is the correct UX model.

It is explicitly different from reusing the same raw private key across curves.

### Current Implementation Note

`xian-py` already demonstrates the conceptual approach:

- Ed25519 wallet derivation
- Ethereum wallet derivation

However, as of this design, the current HD dependency stack on Python 3.14 is
not yet production-ready because the `bip-utils -> coincurve` chain currently
fails to build in local tests.

That is a packaging problem, not a protocol-design problem.

## Genesis And Validator Configuration

Validator configuration must separate:

- validator consensus key
- transaction reward / operator account

Genesis and network manifests should store account-bearing values as canonical
transaction account ids, while validator consensus keys remain their own
separate Ed25519 values.

This prevents accidental coupling between:

- consensus identity
- reward/balance ownership

## Migration Policy

The network must not accept both:

- legacy bare Ed25519 sender strings
- typed `ed25519:` sender strings

for the same account namespace on the same live network without a deliberate
migration, because that creates duplicate identities.

### Clean Migration Rule

For an existing network, the migration must be explicit:

1. rewrite state-bearing account keys from legacy bare form to canonical typed
   form
2. rewrite genesis/config/network manifests that reference those accounts
3. switch transaction validation to typed account ids only

There should be no indefinite dual-mode compatibility layer.

### New Networks

New networks should start with typed account ids only.

## Rejected Alternatives

### Reusing The Same Raw Private Key Across Curves

Rejected because it is:

- nonstandard
- confusing for users and tooling
- fragile for interoperability
- unnecessary when mnemonic-based multi-derivation exists

### Replacing Validator Keys With Ethereum Keys

Rejected because validator consensus identity and user transaction accounts are
different concerns.

### Accepting Bare Untyped Account Strings Long-Term

Rejected because it keeps account-family ambiguity in the protocol and blocks a
clean multi-scheme design.

## Implementation Phases

### Phase 1: Protocol Surface

- add typed account-id parsing and validation
- add `xian_tx_v2`
- add `metadata.auth`
- implement the two auth schemes
- make network auth-scheme policy explicit

### Phase 2: Runtime And Indexing

- update nonce tracking
- update state ownership conventions
- update BDS sender indexing and queries
- update `ctx.signer` / `ctx.caller` expectations in docs and standard
  contracts

### Phase 3: SDK And Wallet UX

- expose typed wallet/account models in `xian-py`
- make dual-account-from-one-mnemonic first-class
- add MetaMask-compatible signing/submission flow for
  `secp256k1_eth_personal_sign_v1`

### Phase 4: Network Rollout

- choose per-network allowed auth schemes
- migrate existing networks explicitly
- document operator and user workflows

## Tested Assumptions

These points were verified locally while preparing this design:

- Ethereum-style recoverable signatures already work in `xian-py` through
  `eth_account.messages.encode_defunct(...)`.
- The recovered address matches the Ethereum wallet address correctly.
- The current Xian transaction-signing basis is the canonical encoded payload
  string built from:
  - `chain_id`
  - `contract`
  - `function`
  - `kwargs`
  - `nonce`
  - `sender`
  - `stamps_supplied`

## Final Recommendation

Implement multi-account support by adding:

- typed account identifiers
- explicit auth schemes
- an explicit new transaction format
- per-network allowed auth-scheme policy

Do not implement it by reinterpreting one raw private key across multiple
curves.
