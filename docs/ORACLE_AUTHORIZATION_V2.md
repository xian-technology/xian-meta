# Oracle Authorization V2

Status: proposed cross-repo protocol; not implemented, enabled or approved for
production. This design is a gate for the optional stable protocol. It does
not change the stock CometBFT 0.40.0 baseline or the meaning of contract `now`.

## Required Guarantee

An external price must be fresh when an honest quorum authorizes the **exact
financial intent**, using authenticated observations and live, bounded clock
uncertainty. A recently received transaction or a cached price passing a
chain-time age check is insufficient.

There is a separate limit: a deterministic verifier cannot prove a finite
wall-clock age at settlement after an arbitrarily long suspension. Pause an
otherwise accepted transcript immediately before settlement, wait, and resume
with identical inputs: its deterministic result is unchanged. Heights, nonces,
signed timestamps and successor checkpoints do not distinguish these cases.
Production must accept authorization-time semantics and cap the exposure of
delayed authorized intents, or require a separately reviewed clock-aware
execution/settlement prerequisite. Do not describe that remaining assumption
as cryptographically enforced.

The current reference oracle stamps reports with chain `now`; its `source`
string is not authenticated market provenance. The reference bootstrap's one
reporter and chain-time age defaults are not a production oracle policy.
Successor checkpoints protect minimum custody periods; they do not establish
external price freshness.

## Stock 0.40 Constraints

- `ExtendVote(H)` may sample clocks and feeds nondeterministically, within a
  strict work/time budget. It must not mutate committed state.
- `VerifyVoteExtension`, `ProcessProposal` and `FinalizeBlock` must remain
  deterministic. They cannot fetch live feeds, read wall clocks, or depend on
  mutable local caches.
- Current-height extensions are unavailable to `FinalizeBlock(H)`.
  `PrepareProposal(H+1)` sees its local extended commit; `ProcessProposal`
  does not receive that extension set. The proposer must carry a bounded
  certificate in block data, which every node independently verifies.
- Official 0.40 self-verifies a nonempty local extension and panics on
  rejection. Extend/verify RPC errors also enter panic paths. An oracle outage
  must produce valid `UNAVAILABLE`, not an RPC error or an intentionally
  invalid extension. Empty extensions never mean approval.
- Canonical extension sign bytes include extension, height, round and chain
  ID, but do not implicitly bind the block hash. The signed application
  payload must bind it. `ExtendVote` does not receive a round argument;
  certificate verification uses the actual extended-commit round.
- Count power and public keys from the authenticated native validator set
  **at H**, respecting Comet's delayed update schedule. Current staking
  membership or an arbitrary RPC response is not a substitute.
- PBTS is absent from this release. The withdrawn 1.x line is not a production
  prerequisite. Even its historical PBTS design did not provide unconditional
  wall-clock freshness after arbitrary pauses or valid re-proposals.

Source checks must use the exact release implementation when bundled prose
disagrees with it, particularly for local self-verification.

## Protocol Objects

All encodings are canonical, bounded and versioned. Prices use integer values
with explicit units/exponents; no floating-point ambiguity is permitted.

| Object | Required contents |
| --- | --- |
| `OraclePolicy` | Chain and genesis/recovery identity, deployment ID, monotonic policy epoch, allowed feeds and publisher key epochs, source diversity, timestamp meaning, age/uncertainty/confidence/dispersion bounds, collateral haircuts, exposure caps and resource limits |
| `SourceObservation` | Exact feed/base/quote, integer price and exponent, confidence/range, observation/publish time semantics, source sequence, publisher key epoch and verifiable signature/proof |
| `FinancialIntent` | Owner signature and nonce, operation, vault/revision, collateral/reserve identity, beneficiary, exact amounts, maximum debt/minimum output, acceptable price bounds, policy epoch and cancellation terms |
| `OracleEndorsement` | Protocol/domain identities, H, block hash, final intent root, observation-bundle hash, policy epoch, approval/status and live clock interval with uncertainty |
| `AuthorizationCertificate` | Same-context endorsements, actual commit round, signer identities and signatures sufficient to verify strictly more than two thirds of authenticated H voting power |

A reusable global "fresh price" permission is forbidden. A fresh time statement
cannot be combined with another observation bundle or another intent.
Provider adapters must establish what a timestamp/signature proves. A vendor
name, HTTPS response or unverified foreign-chain RPC read is not transferable
authentication of a market observation. Actual feed coverage and verification
format remain provider-selection requirements.

Accepted age and clock-uncertainty bounds must be finite. Do not inherit the
reference oracle's `max_age=0` meaning of unlimited age or disabled age checks.

## Lifecycle

### Stage in H

Users stage bounded intents and candidate signed observations. Reserve the
required collateral and debt/draw capacity, but do not mint spendable new debt
or release encumbered collateral. Preserve exact custody and atomic rollback.

Compute the final eligible intent root from committed H-1 state and the exact
ordered proposal. Either implement a bounded, faithful preview or use a typed
staging envelope. Scanning only outer transaction names is insufficient:
nested contract calls must not bypass staging, and failed stages must not
become eligible intents.

Policy for H is the policy committed at H-1, matching the verifier's state.
A proposed policy change cannot change its own extension schema. The initial
rule should make a policy-changing block's financial intents unavailable and
cancel prior-epoch reservations; apply the new policy from the next committed
height. More permissive transitions need separate review.

### Endorse in H

An honest `ExtendVote` samples a live clock interval `[L,U]` and verifies the
exact proposal's source bundle. If source observation time is bounded by
`[o-sigma,o+sigma]`, a conservative age bound is `U - (o-sigma)`. Approve only
when this meets the accepted maximum age and all provenance, future-time,
dispersion, user-bound and collateralization rules pass.

Unavailable feeds, timeout, excessive clock uncertainty, absent preview or
unacceptable observations produce a valid `UNAVAILABLE` record. Clock health
is an explicit operator assumption; signatures cannot establish UTC accuracy
or independent operators by themselves.

`VerifyVoteExtension` validates the record's format, domains, bounds and
internal consistency deterministically. It does not reject a well-formed
negative decision merely to veto the financial action. Every honest generated
record must pass its own verifier, including bootstrap and outage cases.

### Carry and Verify in H+1

The proposer carries the previous commit certificate in a bounded system
envelope. Every node rechecks every counted extension signature and payload,
including data that may have arrived after the minimal commit quorum.
Persist the complete bounded observation bundle and proofs in authenticated H
state, or carry them in H+1 against the bundle hash committed in H. A hash-only
reference must never require live RPC or unavailable historical data during
verification or replay.

Verify upstream canonical, length-delimited sign bytes with actual H/round/
chain ID; exact committed block hash; pending-intent root; observation hash;
policy epoch; unique signer identity; and authenticated H keys/power. Require
**strictly more than two thirds** approving the same intent and bundle.
Equality at two thirds, duplicate identities, mixed quotes, forks, rounds,
heights, policy epochs or old validator sets cannot authorize anything.

Establishing authenticated `V_H` with correct validator-update timing is an
implementation prerequisite, including genesis and rotations. Do not infer
public keys/power from the currently selected staking list or query live RPC
during verification.

### Settle or Cancel in H+1

Use the same deterministic validation in finalization. Settle a valid intent
once, against its signed bounds and reserved revision. Otherwise cancel/refund
with bounded work. Missing certificates, missing approval and oracle outages
must never select a cached-price fallback or halt ordinary consensus.

Initially limit H authorization to the immediate successor H+1. It cannot
authorize newly created H+1 intents. This bounds cross-height reuse and work,
but does not bound physical elapsed time. Reserve, mint, settle, cancel and
refund must remain exactly once across every crash/replay boundary.

Repayment, added collateral and fully debt-free closure remain available
without new price authorization. Borrowing, debt-backed collateral withdrawal,
price-based liquidation and auction pricing all need an exact permit. Relevant
state/revision changes invalidate an intent conservatively; no hidden wrapper
or callback entry point may release value without it.

## Trust, Exposure and Availability

The guarantee depends on less than one third faulty endorsement power,
honestly enforced clock/source bounds, authenticated market observations and
correct policy limits. It certifies freshness at an honest approval **sample**.
A sample-to-sign bound is needed to claim age at signing; an additional
authorization-to-settlement bound is needed to claim age at settlement. Neither
bound can be enforced against arbitrary suspension by this deterministic 0.40
design alone.

Recommended production gate: at least four genuinely independent operators,
accepted source diversity and less than one third faulty power. A single
validator provides one operator's trust, not an independent BFT oracle.
An external committee does not remove that validator's control of the chain.

Cap pending exposure per asset/type and globally. Borrow/withdraw valuations
should use accepted lower price bounds; liquidation should require the vault
to be unsafe even at an accepted upper bound. Large jumps or excessive
dispersion enter `NO_NEW_RISK`. Thresholds, collateral liquidity, depeg handling
and the economic treatment of delayed authorizations require explicit risk
acceptance; this design invents no production defaults.

Persistent state holds policies, reservations, intents, consumed IDs and
authenticated validator snapshots. Live clock health and feed samples must be
re-established after restart. Committed-certificate replay reads no HTTP, clock
or mutable feed cache. Enabled extended-commit history must be included in
future full-store/pruning validation. An application-only recovery genesis
cannot silently recreate prior authorization or native proof history.

## Acceptance Gates

Before enabling production, require all of the following:

1. Accept the authorization-time guarantee, delay counterexample, clock/source
   trust model, independent operators, adapters, risk bounds and exposure caps.
   If unconditional settlement-time freshness is required, reject this stock
   0.40 plan and accept another consensus/execution prerequisite first.
2. Freeze canonical schemas/sign bytes, `V_H` derivation, policy transitions,
   operation state machines and measured resource budgets.
3. Test every domain/context/signature alteration, exact quorum boundary,
   mixed/duplicate signer case, old policy/set, observation timestamp/unit and
   confidence boundary. Pairing a fresh clock statement with an old/different
   quote must fail.
4. Prove all honest outage/timeout records self-verify; deterministic verify,
   proposal and finalization outputs agree under different host clocks,
   locales, cache contents, restart and replay. No expected outage may reach a
   Comet RPC-error/self-rejection panic.
5. Test nested staging, reentry, revision changes, concurrent intents, custody
   failure, omission, cancellation, refunds and exact debt/collateral/supply
   conservation. Safe repayment/deposit paths must remain usable.
6. On stock 0.40, serialize real multi-validator tests for pauses before/after
   preview, sampling, signing, H commit and settlement; long idle/halt;
   source/clock outage; withheld/late certificates; and key/policy/validator
   rotation. Demonstrate both refusal of new stale-price intents and the
   documented late settlement of historical authorizations.
7. Verify WAL, full replay, full-store restore and pruning with vote extensions
   enabled. Replay without clocks/feed access on actual Linux ARM64 and x86-64;
   compare every outcome/root. Benchmark maximum validators, intents,
   observations, signature bytes, cancellation work, CPU and gas.

No implementation or network validation of this proposal is claimed. The
existing timing/retention tests validate the current baseline, not these future
oracle gates.

## Ownership

`xian-stable-protocol` owns financial intents, reserves, risk permits and user
status. `xian-abci` owns bounded extension generation and deterministic proof/
validator-set handling. SDKs and clients own intent signing and pending versus
settled receipts. Stack/configs own controlled activation and real rehearsal;
CLI/deploy/full-store tooling owns enabled-extension recovery. Repo-local
implementation tasks belong in those repos after design acceptance.

## Exact Sources

- [0.40 vote handling and local self-verification](https://github.com/cometbft/cometbft/blob/v0.40.0/consensus/state.go#L2232)
- [0.40 extension execution and RPC error handling](https://github.com/cometbft/cometbft/blob/v0.40.0/state/execution.go#L391)
- [ABCI determinism and coherence requirements](https://github.com/cometbft/cometbft/blob/v0.40.0/spec/abci/abci%2B%2B_app_requirements.md)
- [Canonical extension sign bytes](https://github.com/cometbft/cometbft/blob/v0.40.0/types/canonical.go#L68)
- [0.40 consensus parameters](https://github.com/cometbft/cometbft/blob/v0.40.0/types/params.go)
- [Historical PBTS assumptions](https://github.com/cometbft/cometbft/blob/v1.0.1/docs/explanation/core/proposer-based-timestamps.md), not a deployment recommendation
- [NTS delay/uncertainty limitations](https://www.rfc-editor.org/rfc/rfc8915.html#section-8.6)
- [Current reference oracle](https://github.com/xian-technology/xian-stable-protocol/blob/main/contracts/con_oracle.s.py)
