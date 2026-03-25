# Deterministic Randomness

## Goal

Keep contract randomness deterministic and reproducible across validators while
making the runtime cleaner and the API less misleading.

This design is intentionally **not** a secure-randomness design. It is for
deterministic pseudorandomness only.

## Current Problems

The current implementation in `xian-contracting` has four issues:

1. It uses Python's process-global `random` module.
2. It tracks seeding with a module-global boolean.
3. `random.seed(aux_salt)` treats `aux_salt` like an environment-key lookup
   instead of a literal salt value.
4. The docs describe the seed inaccurately.

There is also an environment mismatch:

- on-chain execution derives randomness from block metadata and transaction
  inputs
- simulation currently uses `secrets.token_hex(...)`, which hides the real
  predictability model

## Product Position

Xian randomness should be documented and treated as:

- deterministic
- public
- reproducible
- suitable for low-stakes pseudorandom behavior
- unsuitable for hidden lotteries, private secrets, validator-proof fair draws,
  or anything that requires unpredictability

High-stakes randomness should use a different pattern:

- commit-reveal
- external oracle
- future threshold/VRF design, if added later

## Runtime Model

Replace the Python-global RNG surface with a Xian-owned deterministic PRNG.

The contract-facing module remains:

```python
import random

random.seed()
random.seed("round-2")
random.getrandbits(k)
random.shuffle(items)
random.randrange(k)
random.randint(a, b)
random.choice(items)
random.choices(items, k=k)
```

But the implementation changes:

- no process-global Python `random` state
- no module-global seeded flag
- one execution-local deterministic RNG state
- explicit reset between top-level executions

## Seed Material

`random.seed(aux_salt=None)` builds its base seed from canonical execution
environment values:

- `chain_id`
- `block_num`
- `block_hash`
- `__input_hash`

If `aux_salt` is provided, it is treated as a **literal salt value** and
appended to the seed material.

This means:

- same transaction and same salt -> same sequence
- same transaction and different salt -> different sequence
- different transactions -> different sequence

The old `AUXILIARY_SALT` environment-key indirection is removed.

## PRNG Choice

Use a Xian-owned hash-stream PRNG based on `sha3_256`.

Reason:

- deterministic across validators
- not dependent on CPython `random` internals
- stable across Python version upgrades
- simple enough to audit

Suggested construction:

- maintain `seed_material`
- maintain a monotonically increasing counter
- produce digest blocks from `sha3_256(f"{seed_material}|{counter}")`
- consume those bytes sequentially as the entropy stream

## Derived Operations

Implement the public operations on top of that byte stream:

- `getrandbits(k)`: consume enough stream bytes for `k` bits
- `randrange(k)`: rejection sampling from `getrandbits`
- `randint(a, b)`: `a + randrange(b - a + 1)`
- `choice(items)`: `items[randrange(len(items))]`
- `choices(items, k)`: repeated `choice`
- `shuffle(items)`: Fisher-Yates using `randrange`

## Validation Rules

- `seed()` must be called before using the module
- `getrandbits(k)`:
  - `k < 0` -> `ValueError`
  - `k == 0` -> `0`
- `randrange(k)`:
  - `k <= 0` -> `ValueError`
- `randint(a, b)`:
  - `a > b` -> `ValueError`
- `choice(items)`:
  - empty sequence -> `IndexError`
- `choices(items, k)`:
  - `k < 0` -> `ValueError`

## Execution Lifecycle

The deterministic RNG state is execution-local and must be reset:

- before top-level contract execution starts
- after top-level contract execution finishes

Nested cross-contract calls within the same transaction continue using the same
execution-local RNG state unless the contract explicitly reseeds.

## Simulation Model

Simulation should stop using random secrets for the randomness environment.

Instead:

- `block_hash` should come from provided block metadata if available
- otherwise it should be deterministically derived from available block context
- `__input_hash` should be deterministically derived from block time plus a
  stable payload hash

This keeps simulation closer to real chain predictability.

## Documentation Requirements

Update the public docs so they state clearly:

- Xian randomness is deterministic and public
- the seed comes from block/environment context plus optional literal salt
- it is not secure randomness
- `random.seed("literal-salt")` resets the sequence for that execution

## Out of Scope

- secure on-chain randomness
- validator-unbiasable randomness
- VRF integration
- oracle design

Those should be designed as separate features.
