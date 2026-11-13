# Numeric specification for xian_vm_v2

This is the protocol specification for the fresh-genesis numeric profile. It
defines the arithmetic, interchange and expected results for conformance.
The genesis manifest selects the profile. The standalone compiler and network
SDKs default to V2. Public `ContractingClient` and `ParallelBatchExecutor`
execution accepts only V2, including the profile of an injected driver.
Low-level native tools select V1 explicitly for historical artifact/state
verification and migration; SDK V1 encoding remains available for historical
signed-payload fixtures. A V2 node must reject incompatible persisted state.

## Values and input

- An integer is a signed mathematical integer with `abs(n) < 2**512`. Both
  endpoints ±(2**512 − 1) are valid. Intermediate calculations may be wider.
  Exposed integer results must fit the same range. Overflow fails the call.
- A decimal is an integer coefficient C divided by S = 10**30 with
  `abs(C) < 10**91`. The largest absolute representable value is
  10**61 − 10**−30. Zero has one value and one wire representation.
- Fractional and scientific source literals construct decimals from the source
  digits, including exponent notation. A trailing fractional zero carries no
  precision. An exact value beyond the range or requiring a 31st fractional
  place fails admission, even if a binary float would round it into range.
  `decimal("1.005")` and `decimal(3)` construct exact decimals.
  `int(decimal("-1.9"))` gives −1. `bool` remains distinct at numeric boundaries.
- Exported decimal parameters accept decimals and exactly representable ints.
  Exported int parameters accept ints. Strings require explicit conversion.
  There is no binary float value, raw Python Decimal value, ambient decimal
  context, implicit bool operand, infinity or NaN.

## Arithmetic

Let a and b denote the exact mathematical input values. Check the final result
range after the indicated rounding. For a decimal result, T(x) denotes
truncation toward zero of x × S, divided by S.

| Operation | Result |
| --- | --- |
| Integer `+`, `-`, `*` | Exact integer. |
| Mixed or decimal `+`, `-`, `*` | Decimal T(a+b), T(a−b), or T(a×b). |
| `/` on any int/decimal pair | Decimal T(a/b). The operands need not fit in decimal separately. |
| `//`, `%` | Integers only. q = floor(a/b), remainder = a − b×q. The remainder has the sign of b or is zero. |
| Numeric comparison | Compare exact values, including mixed int/decimal pairs. |
| `**` and two-argument `pow` | Integer base, nonnegative integer exponent. Result must fit. Zero to the zeroth power is one. Modular exponentiation operates on integers. |
| `mul_div_floor(a,b,d)`, `mul_div_ceil(a,b,d)` | Three ints with d > 0. Return floor or ceiling of a×b/d as an int, with one division. The product can exceed the result range. |
| `sqrt(x)` | Nonnegative int or decimal. Return the largest representable decimal whose mathematical square is ≤ x. |
| `quantize(x, places, mode)` | Return decimal rounded to a multiple of 10**−places. Places is an int in [0,30]. The four modes are `toward_zero`, `floor`, `ceil` and `half_even`. Half-even chooses the nearest multiple, choosing the even coefficient on a tie. |

Zero denominators, invalid types, negative square roots, unknown rounding modes
and out-of-range results fail deterministically. A failed contract call commits
no writes or events. The current V2 policy uses execution revision `xvm-execution-12`, gas schedule
`xvm-gas-6` and bytecode `xvm-2`; the numeric charges below are unchanged since
`xvm-gas-3`. The additional raw computation charge is
96 units for a numeric binary operation, 96 for `quantize` or `sqrt`, and
192 for either `mul_div` helper. Power charges 96 times (1 + the exponent
bit length, capped at 512 bits). These are additions to execution and I/O
charges, not a whole-call chi estimate.
An asset may impose a smaller settlement precision. For fees and allocations
in indivisible units use the appropriate floor/ceil helper.

## Wire representation

The same numeric value encoding applies in nested SDK arguments, signed
payloads, stored values, events and results. Integers within ±(2**53−1) are JSON
integers. Larger integers use `{"__big_int__":"9007199254740992"}`. Decimals
always use an exact tagged string, for example `{"__fixed__":"1.25"}`, even for
whole decimals. Canonical numeric text uses ASCII digits, a leading minus only
for negative values, one zero before a fractional decimal point as needed, and
no redundant leading or fractional trailing zeros, exponent, plus sign or
negative zero. Reserved wrappers have exactly one key. Decimal input conveniences
in an SDK may normalize before signing. A validator rejects noncanonical wire
representations. Plain strings such as `"1.25"` remain ordinary contract strings.
Transaction-envelope fields `nonce` and `chi_supplied` must be nonnegative
safe JSON integers; the wide integer tag is for contract values, not those fields.
A contract-local dictionary can use numeric keys, but dictionaries crossing
the V2 wire boundary must use string keys and cannot impersonate reserved
wrappers. Returning or storing a dictionary with a numeric key fails the call.

## Examples

| Expression | Expected value and type |
| --- | --- |
| `9007199254740993 / 1` | decimal 9007199254740993 |
| `1 / 3` | decimal 0.333333333333333333333333333333 |
| `1 / 10**31` | decimal 0 |
| `10**65 / 10**65` | decimal 1 |
| `-7 // 3`, `-7 % 3` | integers −3 and 2 |
| `mul_div_floor(-5, 1, 2)`, `mul_div_ceil(-5, 1, 2)` | integers −3 and −2 |
| `quantize(1.005, 2, "half_even")`, `quantize(-1.015, 2, "half_even")` | decimals 1 and −1.02 |
| `sqrt(2)` | decimal 1.414213562373095048801688724209 |
| `0.123456789012345678901234567891` | decimal 0.123456789012345678901234567891 |
