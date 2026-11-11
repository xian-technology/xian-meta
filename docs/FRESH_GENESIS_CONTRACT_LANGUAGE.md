# Contract language for a fresh Xian genesis

Proposed 2026-11-11. Select one Python-shaped source language, canonical compiler
and Rust VM at genesis. Use the same compiler and execution rules for local
simulation, SDKs and validators. Pin the profile, IR, numeric encoding and gas
schedule by version. This proposal covers the new chain. Its currency and
streaming contracts are newly authored genesis inputs.

## Numbers

The [numeric protocol specification](NUMERIC_PROFILE_V2.md) defines the V2
operator, rounding, range and wire rules.

Use two arithmetic types, bounded integers and a single fixed-point `decimal`.
Make `amount: decimal` valid in exports and event schemas. Accept ordinary
decimal literal spelling such as `0.05` by reading the source digits directly.
The legacy V1 compiler lowers fractional syntax through binary64. V2 uses
the source token directly; literals and division follow the same exact model.

- Retain Xian's scale of 30 fractional digits and its checked range
  (absolute value below 10^61). Require exactly representable source and input
  values, including exponent notation. Give an error for excess precision.
  Canonicalize equal values, including zero, to one encoding. Use exact tagged
  decimal strings at SDK, transaction, state, event and result boundaries.
- Define `/` for all integer and decimal pairs to return decimal, with one
  truncation toward zero at scale 30. Compute the ratio using bounded wide
  intermediates, including for mixed operands. Check the result range. Reject
  division by zero. Keep integer `//` as mathematical floor and `%` consistent
  with it. Integer smallest units remain appropriate for indivisible assets.
  Keep bool distinct at numeric inputs.
- Expose metered integer `mul_div_floor(a, b, d)` and `mul_div_ceil(a, b, d)`
  with a positive denominator and a single rounding step. Specify fixed
  square root and decimal quantization with an explicit rounding mode. These
  cover AMM shares, debt repayment, fees, auctions and signed prices. A token
  still defines its own settlement precision. A positive quotient below
  10^-30 becomes zero under ordinary division.
- Remove binary float, raw Python Decimal and its context/method catalog from
  this profile. Use one numeric model in annotations, event validation, type
  checks, comparisons, arithmetic, collections and serialized values. Keep
  integer powers and modular arithmetic. Handle additional financial math
  through reviewed, metered functions with known bounds. If a lending or
  weighted-pool implementation needs compound interest or fractional powers,
  test that calculation against published vectors before admitting a primitive.

## What contracts need

| Capability to ship | Decision and reason |
| --- | --- |
| Contract structure and composition | Keep readable functions, loops, comprehensions, assertions, storage, events, caller context, atomic nested calls, dynamic contract lookup and declarative export/interface checks. Routers, marketplaces and schedulers take contract addresses at runtime. Drop mutable interface matchers and callable introspection. |
| Collections | Keep lists, tuples, dictionaries, ordinary membership and iteration over keys, values and items. Define iteration order. Voting and multisig need unique membership. Use keyed storage for persistent membership and a bounded deduplication operation for local input. Omit set/frozenset wire types, dictionary-view algebra, proxy and callable-key behavior. |
| Text, time and signatures | Keep simple interpolation. Provide bounded zero-padding, fixed decimal rendering with explicit precision and rounding, and fixed-width hex. Six presales use two-digit padding. A price oracle signs decimal text, and shielded contracts use 64-digit hex. Keep block time, durations, comparisons and one UTC timestamp parser/renderer (the 14 legacy parsers use `%Y-%m-%d %H:%M:%S`) for vesting and expiry. Omit general format/strftime grammars, locale, debug conversions and host object representations. |
| Binary data and proofs | Keep immutable bytes, hex conversion, metered hashes, signature/proof verification and wide integers. Define a versioned canonical payload encoding with stable key ordering and domain-separated hashes. The scheduler currently distinguishes mutable bytes, sets and binary floats in its digest. Give it a new payload schema and test client/contract byte agreement. |
| Games and governance | Keep deterministic sorting, integer weights, block deadlines and the hashing/signature primitives needed for commit–reveal. Establish the fairness assumptions independently for any randomness API. These products need neither float arithmetic nor a general Python object model. |

## Evidence and migration cost

The xian-1 inventory covered 345 stored sources between heights 4,254,465 and
4,254,469. Counts are per contract, including copies and versions. Of those,
222 reference `float`, 219 in argument annotations, and 14 in runtime type
checks. Categories overlap. No explicit `float()` or `round()` calls were found.
100 contain division or augmented division. Operand types depend on call data.
Four sources have recovery collisions and legacy submission fails current
admission. The other 340 compile and self-validate with the f-string fix.

An isolated native VM prototype changed only integer true division to compute
`trunc(a × 10^30 / b)` as a checked scaled integer. Current and prototype
executions of the four published application workflows produced byte-identical
observation files for all 68 steps, including results, state, writes, events
and expected business failures. Coverage includes reflection transfers, names,
staking and DEX liquidity, swaps and slippage rejection. Several paths already
use fixed decimals. Separate metered contract calls verified positive/negative
thirds, the exact integer 9,007,199,254,740,993 divided by one, a ratio of two
10^65 operands, the smallest unit, underflow to zero, overflow and zero division.
These are local authored calls. Broader behavior, precision-sensitive branches,
fees, ABI validation and gas still need the gates below.

A second prototype admitted `decimal` annotations, removed `float` from the
annotation allowlist, and replaced only `float` identifier tokens in recovered
sources. All 340 baseline-admissible contracts still compiled and self-validated
(220 edited, 120 unchanged). All 68 observations also matched when the four
workflows ran with the edited application sources. Both prototypes used the
previous value codecs and host functions. This established a mechanical first
port and tested one operator change. V2 now implements direct-digit literal
parsing, numeric ABI enforcement and exact wire types. The architecture
decisions below also cover future language cuts.

Three concrete manual review targets are `con_easy_dex` (default integer
slippage divided by 100), `con_price_feed_102025` (decimal text in a signed
message) and `con_ai_dice2` (a raw Decimal constructor in a random-number
calculation). In event type lists, simplify `(int, float, decimal)` to
`(int, decimal)`. In runtime checks, review the intended domain before
collapsing two existing cases into one.

## V2 application results

With the implemented compiler and VM, 339 of the 340 previously admissible
archived sources still compile after a token-level `float` → `decimal` edit.
The remaining source, `con_ai_dice2`, uses a raw Decimal constructor. This
is source admission, not evidence each contract behaves identically.

For behavior, four archived application workflows were run against both metered
VMs, reopening storage between calls: names, reflection token, staking and
DEX. Their 68 steps produced the same numerical balances, allowances, rewards
and liquidity and the same business successes and failures. Ports included
explicit square roots in the DEX. Types did change: exported decimal amounts
can return an integral decimal where V1 returned an int. Four returned messages
changed notation (for example, `Transferred 1E+3` became `Transferred 1000`).
Treat signed or hashed numeric text as a protocol of its own when porting.
These are authored workflows, not a replay of historical transactions.

## Delivery and acceptance

1. **Specify the profile and freeze examples.** In xian-meta and xian-contracting,
   pin the grammar, type/operator table, limits, rounding, error behavior and
   wire vectors. Include literal digits beyond binary64 precision and signed
   payloads. Choose byte-exact expected results before changing implementation.
2. **Implement numbers end to end.** In the compiler, VM and both SDKs, add
   exact literals, the decimal ABI type, division, quantization, and checked
   wide arithmetic. Disallow float and raw decimal values at every entry point,
   including nested containers and host return values. Make the simulator
   execute the same profile. Test Python, JS/WASM and native vectors, failure
   rollback and costs.
3. **Port a representative product per use case.** Provide a syntax-aware
   migration check for annotations, event schemas and type tests. Flag division,
   rounding, signed payloads and digest changes for human review. Exercise the
   DEX, staking, oracle, scheduler, shielded transfer, NFT royalty, weighted
   game and governance vote with realistic and boundary inputs. Keep old/new
   observations and record each intentional difference with its business reason.
   Verify conservation, slippage thresholds, fee beneficiaries and signature
   bytes. A compile-only pass cannot answer those questions.
4. **Cut the excess and launch from fresh genesis.** Once each retained use
   case passes, omit the superseded APIs from compiler admission, host catalog,
   VM values, storage codecs and documentation for the new profile. Confirm
   unsupported programs fail at admission wherever statically decidable. In
   xian-abci and xian-stack, pin the profile and deploy the new system contracts.
   Require identical replay state roots and costs on supported architectures,
   SDK-to-node signature vectors, and a successful clean-genesis rehearsal.

See the [execution profile architecture](CHAIN_EXECUTION_PROFILES_PLAN.md) and
the [shared SDK transaction encoding](TRANSACTION_ENCODING_CONTRACT.md).
