# Deterministic Randomness

The Rust VM owns the `random` syscalls. Each transaction starts with an
unseeded stream shared by nested contract calls and constructors.
`random.seed()` starts or resets that stream using the chain ID, block height,
block hash, and transaction input hash. An optional literal salt can be a
string, integer, boolean, or `None`.

The stream reads SHA3-256 digests of the seed material and an incrementing
counter. Range and selection operations draw from that stream with rejection
sampling. `random.random()` returns the exact decimal
`randbelow(10**30) / 10**30`. The VM checks work bounds before drawing, including
the 512-bit limit for `getrandbits`.

Identical context and inputs reproduce the same sequence. Use this API for
behaviors that tolerate public predictability, such as low-stakes shuffled
ordering. Applications that require unpredictable outcomes need a separate
randomness protocol.

See the [contract developer reference](https://docs.xian.technology/smart-contracts/stdlib/random)
for supported calls and the
[VM implementation and tests](../../xian-contracting/packages/xian-vm-core/src/block_host/random.rs)
for exact stream and error behavior.
