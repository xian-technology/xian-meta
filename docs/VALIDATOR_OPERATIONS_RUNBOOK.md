# Validator Operations Readiness Runbook

This is the cross-repo acceptance checklist for validator lifecycle and
governance operations. It applies to local and private-network rehearsals for
the current codebase. It is not evidence that a public Xian network is live or
ready to accept validators.

The detailed command and contract-call procedures are published in the
`xian-docs-web` [Validator Operations Runbook](../../xian-docs-web/node/validator-operations-runbook.md).
This page defines the evidence a launch owner should require before accepting
those procedures.

## Roles And Evidence

Assign these roles before a rehearsal:

- incident lead: owns stop/go and recovery-plan coordination
- governance proposer: prepares the exact call and impact statement
- independent reviewer: checks chain id, payload, thresholds, and simulation
- validator operators: execute node and wallet steps for their own validator
- recorder: preserves transaction hashes, heights, app hashes, and artifacts

Every rehearsal record should pin:

- network manifest and release-manifest hashes
- chain id and genesis hash
- validator account and consensus-key fingerprints
- start/end heights and app hashes observed by more than one node
- proposal ids, exact payloads, voter records, and transaction hashes
- validator records before and after every lifecycle transition
- pending-unbond ids, amounts, unlock times, and eventual claim results
- incident or recovery-plan artifact hashes when used

Never place validator private keys, wallet seed phrases, or raw signing
material in the evidence bundle.

## Required Drills

### Onboarding

- create and start the node from the pinned private-network manifest
- submit registration with reviewed profile and reward-routing values
- satisfy the configured self-bond and total-bond gates
- exercise the configured admission mode (`manual`, `auto_top_n`, or `hybrid`)
- confirm `pending -> approved -> active` as applicable
- confirm the validator appears in consensus and governance read surfaces
- demonstrate candidate rollback with `unregister()` before activation

### Exit And Unbond

- record registration bond, self-bond, delegation, and delegator ownership
- exercise `announce_leave()` without stopping an active validator early
- exercise a rebalance during the leave delay
- complete `leave()` after the on-chain deadline and confirm terminal `left`
- confirm the registration-bond refund and every generated unbond record
- wait for a rehearsal unlock and claim operator and delegator unbonds

### Jail, Evidence, And Slashing

- exercise governed jail and unjail with reason and before/after records
- inject supported rehearsal evidence through the runtime-owned path
- prove duplicate evidence ids are idempotent
- reconcile live stake and slashable pending unbonds against the infraction height
- reconcile the slash amount at the configured destination
- confirm a jailed validator cannot accept bond or re-enter selection

### Governance Configuration

- simulate and approve a positive registration-fee change, then complete a
  candidate registration using that fee
- simulate a non-empty `update_policy` payload and verify each changed field
- prove malformed, unknown, empty, negative, and wrong-type payloads reject
  before proposal creation
- prove every `change_types` proposal retains the immutable recovery vote set
- record the rollback proposal or forward-fix payload before applying a change

### Incident And Recovery

- exercise a forward state patch while the private network is finalizing
- exercise a coordinated recovery plan from a known-good snapshot while the
  rehearsal network is stopped
- validate trusted height, block hash, app hash, runtime versions, and snapshot
  checksum independently before restore
- confirm every validator returns to the same app hash before reopening traffic

## Acceptance Gate

The runbook is accepted only when all required drills pass twice from the same
pinned release state: once on a five-validator localnet and once on a
private-network topology that includes peer discovery, validator churn, and
snapshot restore.

Open gaps, manual exceptions, or a failed reconciliation keep the gate open.
Changing code, contract source, release pins, genesis, or operator procedure
invalidates the prior result and requires another rehearsal.
