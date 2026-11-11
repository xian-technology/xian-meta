# Transaction encoding across SDKs and the node

The current Python and JavaScript SDK sources default to `xian_vm_v2` for fresh-chain
transactions. Both node admission paths verify the same canonical bytes.

## V2 contract values

- Encode integers in the inclusive range from `-(2**53 - 1)` to `2**53 - 1`
  as JSON integers. Larger magnitudes up to `2**512 - 1` use a single-key
  object containing signed decimal integer text, such as
  `{"__big_int__":"9007199254740992"}`. Use Python `int` or JavaScript
  `bigint` when constructing a wide integer in application code.
- Encode every decimal as a tagged plain string, including whole values.
  `{"__fixed__":"1"}` represents decimal one, `1` represents integer one,
  and `"1"` remains a string. A canonical decimal has at most 30 fractional
  places and magnitude below `10**61`. Spell zero `"0"` and omit exponents,
  plus signs, redundant leading zeros and trailing fractional zeros.
- Apply these rules recursively in lists and dictionaries. JSON booleans
  remain booleans. The validator rejects bare fractional numbers and
  noncanonical numeric wrappers. The numeric specification also describes
  dictionary keys, other reserved tags and exact source literals.
  [V2 numeric specification](NUMERIC_PROFILE_V2.md)
- Encode the envelope fields `nonce` and `chi_supplied` as bare JSON integers
  from `0` to `2**53 - 1` inclusive.

## Signing and submission

Sort JSON object keys by Unicode code point at every depth, including
numeric-looking string keys. Preserve each own property as data, including
`__proto__`. Sign the compact canonical UTF-8 JSON payload. Serialize the
complete signed transaction the same way, then submit the ASCII bytes of
its lowercase hexadecimal encoding to CometBFT.

The V2 fixtures specify each payload, signature and full signed transaction.
ABCI parity tests construct transactions using each SDK's default, compare
their submitted bytes to those fixtures and pass them through the Python
and native validators. [V2 transaction fixtures](https://github.com/xian-technology/xian-contracting/blob/main/tests/fixtures/transaction_numeric_v2.json)

## V1 compatibility

To reproduce V1 signing fixtures, select `vm_profile="xian_vm_v1"` in the Python
network SDK or `vmProfile: "xian_vm_v1"` in the JavaScript client. This encoding
option does not enable V1 execution in `ContractingClient` or
`ParallelBatchExecutor`. V1 has its own
normalization and integer-wrapper boundaries. Its golden fixture preserves
expected historical signatures, submitted bytes and CometBFT receipts.
The V1 fixtures come from earlier development and test configurations.
[V1 transaction fixtures](https://github.com/xian-technology/xian-contracting/blob/main/tests/fixtures/transaction_wire.json)

Python storage encoding and wrapper conversion are consensus-sensitive shared
runtime behavior. Changes require encoding tests, SDK preparation tests, node
validation, and the relevant execution tests. Network rollout must use compatible
runtime packages throughout; this contract does not authorize a public launch.

Bundle source validation remains owned by `xian-cli.contract_bundles`. Product
bootstraps consume that validator in their deploy dependency group, resolve
paths/order/budgets from the bundle, and retain the exact verified source bytes
for submission. Product constructors and configuration remain repo-local.
