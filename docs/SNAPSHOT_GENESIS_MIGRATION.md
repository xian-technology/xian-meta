# Snapshot to genesis migration

The new network starts from fresh contracts and imports native currency balances.
It does not import old contract code, approvals, permits, stream obligations,
nonces, account-registry records, or an old chain's genesis allocation formula.
Existing 64-character hexadecimal account identifiers remain byte-for-byte
unchanged, including case. Their existing private keys authorize ordinary
transactions until the owner later enrolls in hybrid authentication. Enrollment
is closed in the initial genesis. No key conversion or claim transaction is
required to receive imported funds.

## Inputs and review

Use a finalized, independently verified source snapshot at one chain ID, height
and block hash. Freeze the source migration accounting at that height: later
old-chain transfers do not alter the new-chain allocation. A file hash pins the
export; it does not prove source-chain consensus or completeness. Compare the
export against multiple independent nodes and reconcile total supply, circulating
balances, escrow liabilities, staking and selected contract holdings before
accepting it. A second transfer/claim process must never credit the same funds.

`xian.currency_snapshot.v1` contains `chain_id`, positive integer `height`,
64-hex `block_hash`, `scope` (`complete` or `sample`), decimal-string `total_supply`, and a `balances` array of
objects with exactly `account` and `amount`. Include every native balance,
including contract-held balances. Amounts are unsigned fixed-point decimal
strings with at most 30 fractional and 61 integral digits; JSON floats are not
accepted. Duplicate JSON keys and duplicate balance accounts are errors.

`xian.balance_migration.v1` contains `source` (the exact `chain_id`, `height`,
`block_hash` and `sha256` of the snapshot file), a distinct `target_chain_id`,
and `contract_dispositions`. Each nonzero non-account balance requires a
separate disposition with a nonempty `reason` and `balances` map. Each map must
sum exactly to its source holding. Destinations may be existing account addresses
or explicitly deployed contracts in the target bundle. User account balances
cannot be redirected. The obsolete `team_lock` name is not a target contract;
any funds held there require an explicitly reviewed distribution. Never invent
its beneficiaries or silently burn the balance.

Selected contracts are deployed from reviewed current source in the genesis
bundle. Funding a name reserved for deployment after launch is disallowed:
someone could capture that name, or its future constructor could make the funds
inaccessible. A source escrow or staking contract cannot simply lose liabilities
while its balance moves to an operator. Its beneficiary accounting and any
replacement constructor state need a separate reviewed allocation decision.
No arbitrary historical state is copied by this tool.

## Build and verify

`xian network migrate-balances --snapshot snapshot.json --plan plan.json
--contracts-dir /path/to/xian-configs/contracts --bundle mainnet --output-dir
/path/to/new-output` creates a self-contained contract directory with a
reconciled bundle, `migration-report.json`, and the exact snapshot and plan.
The command requires a new output directory and publishes it atomically only
after successful reconciliation. Use its bundle through the existing genesis
builder's contracts-directory override. The canonical mainnet bundle stays
`pending_snapshot` and refuses genesis construction until replaced by this
reviewed output; no placeholder allocation is launchable.

Legacy raw BDS rows can first be converted with `xian network
convert-legacy-balances`. This recognizes the old balance/allowance shared hash,
normalizes Decimal signed zero and scientific notation without rounding, and
requires a caller-supplied total. A sample requires `--rehearsal` during migration.
Rehearsal reports never approve launch or claim source consensus verification.

Build the reviewed output with `xian network build-genesis --contracts-dir
/path/to/migration-bundle --bundle mainnet --chain-id TARGET_CHAIN_ID
--genesis-time ACCEPTED_UTC_TIME --output /path/to/new-genesis.json`.
Use an explicit identical time for constructor execution and the CometBFT header.
The command refuses to overwrite an existing file. Do not build the final genesis
until the snapshot and launch configuration are accepted.

The generated bundle pins source hashes and a snapshot/plan hash, exact imported
balances and total, target chain ID, and `_accounts.policy` with enrollment false.
The genesis builder rechecks reconciliation and source hashes, rejects currency
constructor overrides, and verifies actual post-constructor balances, supply,
empty approvals and absent account records. Operators must compare final genesis
state and its hash independently; the report is evidence, not launch approval.

## Launch gates

Final source snapshot and contract dispositions are not yet supplied. Keep
mainnet configuration pending and enrollment disabled. Before launch: approve
the source cutoff and beneficiary accounting, review every selected contract's
spending authority, pin all deployment artifacts, then rehearse the exact final
genesis with five validators, fees, restarts and backup restoration. Check old
private-key spending and balances before enrollment, and verified hybrid backup
and recovery afterwards on disposable fixtures. Independent security review,
physical wallet failure testing and performance/DoS checks remain enrollment
gates. Contract permits and stream relays are removed; direct transaction
caller authorization works with both unenrolled and hybrid accounts. This does
not make validator consensus keys or unrelated cryptographic protocols quantum
resistant.

Complete snapshots also include `contracts`, the full source-contract name
inventory at the cutoff. Pass its JSON array file to the converter using
`--contract-inventory source-contracts.json`. This distinguishes a hexadecimal
contract name from an actual user account; such a contract's funds still require
an explicit disposition. New genesis contract names cannot collide with account
address syntax. Inventory completeness is part of independent source verification.
