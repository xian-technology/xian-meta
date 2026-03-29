# IntentKit Stack Integration

## Goal

Integrate `xian-intentkit` cleanly into the Xian technology stack without
turning it into another repo-local subsystem of `xian-stack`.

The design constraint is important:

- `xian-intentkit` is its own product and repo
- it changes independently
- the Xian stack should manage it without copying its internals

## Ownership

### `xian-intentkit`

- owns its own Compose topology
- owns its own app env contract
- owns its own backend, frontend, and channel services
- remains consumable outside the Xian node stack

### `xian-stack`

- owns the adapter layer
- owns the generated env handoff for stack-managed runs
- owns the published local ports for stack-managed runs
- owns backend start/stop/status/endpoints/health integration

### `xian-cli`

- owns the operator-facing flags and node-profile fields
- persists whether stack-managed `xian-intentkit` is enabled for a node profile
- passes that posture into the `xian-stack` backend

## Integration Contract

The stack-managed integration uses these principles:

1. `xian-stack` does not copy `xian-intentkit` services into its own main
   Compose file.
2. `xian-stack` runs `xian-intentkit` as a separate Compose project with a
   thin stack-owned override file.
3. `xian-stack` generates `xian-intentkit/deployment/.env` from
   `xian-intentkit/.env.example`, current operator env, and stack-derived Xian
   values.
4. `xian-cli` stores only the operator-level posture in the node profile:
   enabled flag, network slot, and published ports.

That preserves repo independence and keeps merge pressure low when the upstream
IntentKit repo changes.

## Network Slot Mapping

`xian-intentkit` currently exposes four Xian slots:

- `xian-mainnet`
- `xian-testnet`
- `xian-devnet`
- `xian-localnet`

The stack-level mapping is:

- canonical mainnet node -> `xian-mainnet`
- canonical testnet node -> `xian-testnet`
- canonical devnet node -> `xian-devnet`
- local or private stack-managed network -> `xian-localnet`

`xian-localnet` is the generic private-network slot for stack-managed and
operator-managed Xian deployments that are not one of the canonical public
networks.

## Pricing Contract

USD pricing is deployment-specific, not baked into the stack.

The stack adapter passes through these deployment values:

- `XIAN_INTENTKIT_PRICE_STRATEGY`
- `XIAN_INTENTKIT_PRICE_FIXED_USD`
- `XIAN_INTENTKIT_PRICE_SOLANA_MINT`
- `XIAN_INTENTKIT_PRICE_MARKET_URL`

The adapter writes those into the selected network slot inside
`xian-intentkit/deployment/.env`.

This keeps `xian-intentkit` generic while still allowing the live Xian network
deployment to use the bridged Solana token for pricing.

## Service-Node Note

Basic Xian wallet and transaction flows only need RPC reachability.

Indexed Xian features inside `xian-intentkit` are strongest when the node is a
service node with BDS enabled, because event and indexed-transaction paths rely
on the ABCI query surface exposed by that posture.
