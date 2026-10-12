# Transaction encoding across SDKs and the node

The Python and JavaScript SDKs and both node validation paths share the same
normalized transaction wire contract. Authoritative golden cases live in
`xian-contracting/tests/fixtures/transaction_wire.json`; the SDK and ABCI tests
read that fixture from the sibling checkout. This keeps expected signing bytes
and submitted bytes independently reviewable instead of reproducing an encoder
inside each test suite.

- JSON object keys are sorted by Unicode code point at every depth. Numeric
  strings are ordinary keys for canonicalization, regardless of JavaScript's
  object enumeration rules.
- Own object keys are preserved as data, including `__proto__`. Copying or
  decoding an object must not invoke a prototype setter.
- Runtime wrappers are normalized recursively through lists and dictionaries.
  The integer wrapper rules preserve existing signed 64-bit boundary behavior;
  JavaScript also wraps integers outside its safe numeric range. Use native
  `bigint` to avoid precision loss before serialization. These representations
  can differ before normalization; the fixture specifies exact normalized inputs.
- Booleans remain booleans. Node transaction rules continue to reject bare
  floating-point values and enforce the canonical JSON integer bounds.
- Sign the canonical UTF-8 payload string. Serialize the whole signed transaction
  canonically, then submit the ASCII hex encoding of its UTF-8 bytes to CometBFT.
- Nodes retain strict canonical-byte validation. SDK bugs must be fixed at the
  producer rather than bypassed at admission.

Python storage encoding and wrapper conversion are consensus-sensitive shared
runtime behavior. Changes require encoding tests, SDK preparation tests, node
validation, and the relevant execution tests. Network rollout must use compatible
runtime packages throughout; this contract does not authorize a public launch.

Bundle source validation remains owned by `xian-cli.contract_bundles`. Product
bootstraps consume that validator in their deploy dependency group, resolve
paths/order/budgets from the bundle, and retain the exact verified source bytes
for submission. Product constructors and configuration remain repo-local.

The explicit [account-registry envelope](ACCOUNT_REGISTRY_PROTOCOL.md) uses the
same canonical JSON and ASCII-hex transport, with its own framed hybrid signing
messages. It preserves existing sender strings. Legacy envelopes retain their
current encoding and are valid only for unenrolled accounts. Registry policy is
not installed by default.

Hybrid epochs retain raw uint64 JSON integer tokens rather than runtime
`__big_int__` wrappers. JS uses `canonicalAccountJson` for the hybrid envelope.
Hybrid broadcasts use a JSON-RPC POST body to avoid URL/header limits for the
larger proofs: `params.tx` is base64 of the **ASCII hex transaction bytes**, not
base64 of JSON. This does not change the CometBFT transaction bytes or hash.
