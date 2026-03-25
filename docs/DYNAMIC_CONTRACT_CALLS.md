# Dynamic Contract Calls

Status: proposed

This document defines a secure way to let contracts call exported functions by
string name at runtime.

The goal is to support patterns like:

- dynamic token adapters
- registry-driven dispatch
- plugin/module architectures
- factories that route to child contracts by configuration

without turning the contract runtime into a generic reflection surface.

## Problem

Xian already allows dynamic contract selection:

```python
t = importlib.import_module(contract_name)
return t.balance_of(account=account)
```

That means the contract name can come from state or function arguments.

What is still missing is dynamic function selection. Today contracts cannot
cleanly do:

```python
function_name = "balance_of"
# not currently supported
```

The obvious way to add this would be to allow generic `getattr(...)` on the
imported module. That is the wrong design.

## Decision

Xian should add an explicit helper to the contract `importlib` bridge:

```python
importlib.call(contract, function, kwargs={})
```

Where:

- `contract` is either a contract name string or a previously imported contract
  module
- `function` is the exported function name as a string
- `kwargs` is a dictionary of keyword arguments

This helper must only resolve exported callable contract functions. It must not
expose generic attribute lookup.

## Why `getattr` Is The Wrong Primitive

Adding generic reflective lookup would create a much larger surface than the
feature actually needs.

Problems with a generic `getattr` path:

- it makes it easier to push the runtime toward Python-style reflection instead
  of Xian's constrained contract model
- it creates ambiguity between callable exports and non-callable module-level
  objects
- it is harder to enforce “exported functions only” as an explicit policy
- it weakens future security boundaries because any later module attribute
  becomes dynamically reachable by string

An explicit `importlib.call(...)` keeps the capability narrow and auditable.

## Current Runtime Facts

These implementation facts matter for the design.

### Dynamic contract selection already exists

The current bridge already supports:

- `importlib.import_module(name)`

See:

- [imports.py](/Users/endogen/Projekte/xian/xian-contracting/src/contracting/stdlib/bridge/imports.py)

### Exported functions are visible on imported modules

Exported functions appear as callable attributes on the loaded contract module.

### Non-export helper functions are not exposed the same way

A local runtime check on `2026-03-25` showed that a non-export helper defined
inside a contract does not appear as a callable attribute on the imported
module, while the exported function does.

That is good. It means a dynamic call helper can safely resolve from module
attributes as long as it still verifies the target is an exported function.

### Context switching already happens through the export wrapper

Cross-contract call context today is enforced by the `@__export(...)` wrapper:

- [access.py](/Users/endogen/Projekte/xian/xian-contracting/src/contracting/stdlib/bridge/access.py)

So the safest way to implement dynamic calls is to resolve the existing export
wrapper and call it, not to bypass it.

## Goals

- allow dynamic exported function calls by string
- preserve current `ctx` semantics exactly
- preserve owner checks exactly
- preserve private-function restrictions
- preserve deterministic rollback behavior
- avoid exposing generic reflection
- keep the contract-facing API small

## Non-goals

- no generic `getattr`, `dir`, or attribute enumeration surface for contracts
- no dynamic access to state variables by string in v1
- no positional-argument calling path in v1
- no private-function access by string
- no new bypass around the existing export wrapper

## Public API

The proposed contract-side API is:

```python
importlib.call(contract, function, kwargs={})
```

### Accepted inputs

`contract`:

- `str`: contract name
- `ModuleType`: a contract module previously returned by `importlib.import_module(...)`

`function`:

- `str`

`kwargs`:

- `dict`
- keys must be strings

### Examples

By contract name:

```python
@export
def balance_for(contract_name: str, account: str):
    return importlib.call(
        contract_name,
        "balance_of",
        {"account": account},
    )
```

Using a previously imported module:

```python
@export
def call_known(module_name: str, function_name: str, account: str):
    m = importlib.import_module(module_name)
    return importlib.call(
        m,
        function_name,
        {"account": account},
    )
```

## Resolution Rules

The helper must resolve the target in this order:

1. resolve the contract module
2. validate the function name
3. resolve the attribute from the module
4. verify that the attribute is an exported callable
5. validate kwargs against the original exported function signature
6. call the exported wrapper

### 1. Module resolution

If `contract` is a string:

- reuse the same validation rules as `importlib.import_module(name)`
- reject invalid names
- reject stdlib/builtin module names
- reject missing contracts

If `contract` is a module:

- require `ModuleType`
- require that the module name resolves to an existing deployed contract in the
  current driver

### 2. Function-name validation

The helper must reject function names that:

- are not strings
- are empty
- start with the private prefix (`__`)
- start or end with `_`
- are not valid identifiers

This mirrors the existing contract-subset naming rules and blocks any attempt
to dynamically target private/internal names.

### 3. Attribute resolution

Resolve with:

- `vars(module).get(function_name)`

Do not use generic Python reflection beyond this narrow lookup.

### 4. Exported-callable verification

The resolved attribute must satisfy all of these:

- it is a `FunctionType`
- it is an exported contract function wrapper
- it is not a plain helper or non-callable datum

Implementation detail:

- exported functions today are wrapped by `@__export(...)`
- the wrapper closes over the original function
- this can be verified by checking the closure and unwrapping the original
  function object

The helper should use a shared internal resolver such as:

- `_resolve_exported_function(module, function_name)`

That resolver should return:

- the callable export wrapper
- the original function object

This keeps the contract call path and any future interface helpers consistent.

### 5. Argument validation

Before calling the wrapper, the helper should validate `kwargs` against the
original function signature.

Use the original function object, not the wrapper, so that:

- unexpected keys fail cleanly
- missing required args fail cleanly
- defaults are handled correctly

The intended implementation is:

- `inspect.signature(original).bind(**kwargs)`

This is better than letting arbitrary keyword mismatches trickle through the
wrapped call path.

### 6. Invocation

The helper must call the resolved export wrapper directly:

- `return wrapper(**kwargs)`

This guarantees that:

- `ctx.caller` updates the same way as today
- `ctx.signer` remains unchanged
- `ctx.entry` remains unchanged
- owner checks remain enforced
- rollback behavior remains unchanged

## Security Model

### Exported functions only

Dynamic calling must not expose:

- non-export helper functions
- module-level variables
- `Hash` / `Variable` objects
- private functions

That is the main security boundary.

### No new authority

This feature does not create a new permission class.

If a contract could statically do:

```python
import target
target.transfer(...)
```

then dynamic call simply lets it choose the exported function name at runtime.

The called contract still controls:

- owner checks
- business logic checks
- allowance/authorization checks

### No reflection escalation

Because the API is a dedicated `importlib.call(...)` helper instead of generic
attribute reflection:

- the runtime does not become a general introspection environment
- later module attributes do not automatically become dynamically reachable

### Determinism

The helper uses deterministic local data only:

- current contract module state
- current deployed contract state
- Python signature metadata already present in the loaded function object

No nondeterministic host behavior is introduced.

### Metering

No special metering path is required in v1.

The helper adds only small host-side resolution overhead compared with the
existing dynamic import path. The meaningful execution cost still happens inside
the called contract under the normal tracer and write/read metering rules.

If future benchmarking shows the signature-resolution path matters, the runtime
can add a tiny fixed dynamic-call surcharge. That is not necessary for v1.

## Context Semantics

Dynamic calls must be identical to normal cross-contract calls.

If `con_router.route("con_token", "balance_of", {"account": "alice"})` is
called by signer `bob`, then inside `con_token.balance_of(...)`:

- `ctx.this == "con_token"`
- `ctx.caller == "con_router"`
- `ctx.signer == "bob"`
- `ctx.entry == ("con_router", "route")`

No special-case context semantics should exist for dynamic calls.

## Failure Semantics

The helper should fail loudly and atomically.

Examples:

- invalid contract name -> `ImportError` / assertion failure
- missing function -> exception
- target is not an exported callable -> exception
- bad kwargs -> exception
- called contract reverts -> exception

As with normal cross-contract calls, all state changes in the current
transaction must roll back on failure.

## Compatibility With Existing Patterns

This feature complements the current dynamic-import pattern.

Today:

```python
t = importlib.import_module(tok)
return t.balance_of(account=account)
```

With the new helper:

```python
return importlib.call(tok, "balance_of", {"account": account})
```

The old pattern should continue to work. The new helper just fills the missing
case where the function name is only known at runtime.

## Optional Small Improvement

As a follow-up, the bridge can also add:

```python
importlib.has_export(contract, function)
```

This would be a convenience helper for routers and adapters, built on the same
internal export resolver.

This is not required for v1. The minimal valuable feature is `importlib.call`.

## Implementation Plan

### `xian-contracting`

Update:

- [imports.py](/Users/endogen/Projekte/xian/xian-contracting/src/contracting/stdlib/bridge/imports.py)

Add:

- module resolver for `str | ModuleType`
- exported-function resolver
- signature validation
- `call(...)`

Likely internal helpers:

- `_resolve_module(target)`
- `_unwrap_exported_function(function_name, attribute)`
- `_resolve_exported_function(module, function_name)`

### Tests

Add integration coverage for:

- dynamic call by contract-name string
- dynamic call by imported module object
- private function rejection
- helper/non-export function rejection
- bad kwargs rejection
- owner-gated dynamic call still enforcing owner semantics
- context semantics matching normal cross-contract calls

## Recommendation

Add `importlib.call(...)`.

Do not add generic `getattr` support to smart contracts.

That gives Xian the missing dynamic-dispatch capability while keeping the
runtime narrow, deterministic, and explicitly policy-controlled.
