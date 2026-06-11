# Xian x402 Exact Payment Profile

## Status

Milestone 1 implemented — the profile ships as `xian_py.x402` (sign / verify /
facilitator helpers), the `examples/x402_exact/` reference set in `xian-py`,
and x402 canary phases in the `xian-stack` localnet e2e. Kept as the design
record for the profile.

This document defines the first native-Xian profile for x402-style HTTP
payments. It is intentionally narrow: fixed-price `exact` payments, Xian
Ed25519 accounts, Xian token contracts that expose the XSC001 allowance
surface, and facilitator-mediated settlement.

The goal is to prove that Xian can participate in the HTTP 402 payment loop
without changing consensus, token contracts, or the browser wallet provider
surface first.

## Scope

This profile applies to:

- `xian-configs`: settlement contract and example metadata
- `xian-py`: buyer, seller, and facilitator helpers
- future `xian-wallet-browser` work: typed payment approvals
- future `xian-intentkit` work: native-Xian x402 skills

## Non-Goals

- usage-based `upto` payments
- streaming payments
- multi-token price discovery
- direct integration with the upstream x402 SDK registry
- consensus-level transaction or account changes
- browser-wallet UI changes in milestone 1

## Protocol Fit

x402 defines the HTTP loop:

1. client requests a protected resource
2. server returns `402 Payment Required`
3. server includes a base64 JSON `PAYMENT-REQUIRED` header
4. client retries with a base64 JSON `PAYMENT-SIGNATURE` header
5. server verifies and settles locally or through a facilitator
6. server returns the resource with a base64 JSON `PAYMENT-RESPONSE` header

The Xian profile uses that transport shape but defines a Xian-specific payment
mechanism under the `xian:<chain_id>` network namespace.

## Network And Asset Identifiers

The milestone 1 network id is:

```text
xian:<chain_id>
```

Examples:

- `xian:xian-local-1`
- `xian:xian-devnet-1`

The asset id is the Xian token contract name:

```text
currency
con_usdc
```

Production adoption should eventually pursue a formal x402 network
registration path. Until then, `xian:*` is an experimental profile namespace.

## Payment Requirement

The server advertises one or more accepted payment options. Milestone 1 emits
one fixed-price option:

```json
{
  "x402Version": 2,
  "accepts": [
    {
      "scheme": "exact",
      "network": "xian:xian-local-1",
      "asset": "currency",
      "maxAmountRequired": "0.001",
      "payTo": "<seller account>",
      "resource": "https://api.example.test/data",
      "settlementContract": "con_x402_settlement",
      "description": "Paid API request"
    }
  ],
  "extensions": {
    "payment-identifier": {
      "required": true
    }
  },
  "error": ""
}
```

Amounts are canonical decimal strings. Floats are not part of the wire format.

## Payment Payload

The client retries the request with `PAYMENT-SIGNATURE` containing base64 JSON:

```json
{
  "x402Version": 2,
  "scheme": "exact",
  "network": "xian:xian-local-1",
  "asset": "currency",
  "amount": "0.001",
  "payTo": "<seller account>",
  "resource": "https://api.example.test/data",
  "payer": "<buyer account>",
  "paymentId": "pay_<random>",
  "deadline": "2026-05-07 12:30:00",
  "settlementContract": "con_x402_settlement",
  "signature": "<buyer signature over x402 payment>",
  "permitSignature": "<buyer signature over permit_authorizer approval>",
  "extensions": {
    "payment-identifier": {
      "id": "pay_<random>"
    }
  }
}
```

The two signatures are deliberate:

- `signature` binds the x402 commercial terms: resource, seller, amount, token,
  payment id, deadline, network, and settlement contract.
- `permitSignature` authorizes the existing `permit_authorizer` contract to
  approve `con_x402_settlement` for exactly the same amount.

This lets the facilitator submit one settlement transaction on behalf of the
buyer without requiring a prior `approve(...)` transaction.

## Settlement Contract

`con_x402_settlement` verifies and settles in one exported function:

1. check `scheme == "exact"`
2. check `network == "xian:" + chain_id`
3. check `settlementContract == ctx.this`
4. check `paymentId` has not been settled
5. check deadline
6. verify the x402 payment signature
7. call `permit_authorizer.permit(...)`
8. call `token.transfer_from(...)`
9. mark the payment id settled
10. emit `X402PaymentSettled`

The server or facilitator must still keep an off-chain idempotency cache so a
retry with the same payment id can return the cached resource instead of
attempting settlement again.

## Trust Boundaries

- The buyer signs both payment and permit payloads.
- The seller defines the advertised payment requirements.
- The facilitator verifies signatures and submits settlement, but cannot change
  payee, amount, token, resource, deadline, or payment id without invalidating
  the buyer signature.
- The settlement contract is the final authority on replay prevention and token
  movement.
- The resource server is responsible for caching fulfilled payment ids.

## Milestone 1 Deliverables

- `x402_settlement.s.py` in `xian-py/examples/x402_exact/contracts`
- `xian-py` helpers for requirement encoding, payment signing, verification,
  settlement, and paid HTTP requests
- a FastAPI seller/facilitator example under `xian-py/examples/x402_exact`
- an example contract source under `xian-py/examples/x402_exact/contracts`

## Later Work

- browser wallet typed approval view for x402 payloads
- `xian-js` equivalent helpers
- IntentKit native-Xian x402 skill
- upstream x402 scheme registration or adapter
- stablecoin-oriented token template with decimal metadata
- `upto` usage-based settlement after exact payments are proven
