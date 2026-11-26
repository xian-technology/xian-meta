# Shared Foundations Decision

The shared Python package split is implemented. Both packages live under
`xian-contracting/packages/`:

- [`xian-accounts`](../../xian-contracting/packages/xian-accounts/README.md)
  owns Ed25519 key and signing primitives. The node uses it directly, and
  the Python SDK wraps it for its wallet API.
- [`xian-runtime-types`](../../xian-contracting/packages/xian-runtime-types/README.md)
  owns deterministic runtime value types and wire encoding for Python
  consumers.

This split keeps transaction-account helpers separate from deterministic
runtime value semantics. The node can use both packages without importing
the application SDK.

The contract decompiler was retired. Source-backed deployment persists
canonical source alongside IR, and source queries read the stored source.

[Shared Package Extraction Plan](SHARED_PACKAGE_EXTRACTION_PLAN.md) records the
conditions for revisiting repository ownership.
