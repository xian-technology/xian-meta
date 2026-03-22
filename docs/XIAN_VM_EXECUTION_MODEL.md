# Xian VM Execution Model Design

## Status

Proposed implementation target.

This document defines the target design for a future Xian-owned contract
execution engine where Python remains the authoring language, but contract
execution and metering no longer depend on CPython bytecode semantics or Python
runtime tracing.

It is intended to be precise enough to implement against without inventing
additional consensus-relevant behavior during implementation.

## Scope

This design applies to:

- `xian-abci`
- `xian-contracting`
- `xian-py`
- `xian-cli`
- `xian-configs`
- `xian-stack`
- `xian-docs-web`

## Goals

- Make contract execution semantics a Xian-defined machine contract, not a
  CPython implementation detail.
- Preserve Python-like contract authoring for developers.
- Replace tracer-based metering with direct VM-level metering.
- Keep execution deterministic across validators and across supported Python
  toolchain versions.
- Make future optimization possible without changing contract source language.
- Make runtime behavior stable even when CPython bytecode or monitoring details
  change.
- Support eventual native execution in Rust without requiring CPython during
  contract execution.

## Non-Goals

- Running arbitrary Python inside the VM.
- Supporting the full Python language or Python standard library.
- Preserving CPython bytecode as a consensus or on-chain execution format.
- Preserving CPython opcode cost schedules as the long-term gas model.
- Requiring `xian-contracting` to stop offering the current pure-Python default
  before the VM is production-ready.
- Migrating existing contracts silently or heuristically.

## Core Decisions

1. Python remains the contract source language frontend.
2. Xian execution no longer depends on the CPython VM in the target model.
3. Xian defines its own restricted language subset, semantic IR, and execution
   machine.
4. The first Xian VM is a stack machine.
5. Contracts compile from Python AST into a versioned Xian IR and then into a
   versioned Xian bytecode format.
6. Metering is defined on VM instructions and explicit host syscalls.
7. All external effects are explicit host syscalls. Contract code cannot touch
   host resources directly.
8. Contract-visible context such as `ctx`, `now`, and block metadata is
   provided by the host environment, not by Python globals.
9. Xian VM version, bytecode version, and gas schedule are network execution
   policy.
10. Existing CPython-based execution remains a separate engine until the VM has
    parity and a deliberate rollout path.

## Terminology

- `source language`: the Python-like language written by contract authors.
- `frontend`: the parser, validator, and lowering stages that convert source
  code into Xian IR.
- `Xian IR`: a structured, versioned intermediate representation with Xian
  semantics, independent of CPython bytecode.
- `Xian bytecode`: a compact, versioned executable representation consumed by
  the VM.
- `VM`: the Xian virtual machine that executes Xian bytecode.
- `host`: the blockchain execution environment that provides state, events,
  context, and metering policy.
- `host syscall`: an explicit VM operation that requests host behavior such as
  reading state or emitting an event.
- `execution engine`: a concrete runtime implementation, for example the
  existing CPython-backed engine or a future `xian_vm_v1`.
- `gas schedule`: the versioned mapping from VM instructions and syscalls to
  stamps.

## Why Python Becomes A Frontend

Today the execution model is effectively:

- write Python
- compile to CPython bytecode
- execute in the Python runtime
- meter execution indirectly through tracing or monitoring

The target model is:

- write Python-like Xian contracts
- parse and validate restricted Python source
- compile to Xian IR
- compile or lower to Xian bytecode
- execute Xian bytecode in the Xian VM
- meter VM instructions and host syscalls directly

In this model, Python remains the developer-facing authoring language, but it
is no longer the runtime or consensus machine.

The practical meaning is:

- CPython is a build-time frontend tool, not the contract execution engine.
- contract semantics are defined by the Xian language subset and VM spec, not
  by CPython bytecode details.
- gas semantics belong to Xian itself, not to Python tracing callbacks.

## High-Level Architecture

The target execution pipeline is:

1. Source parse
2. Source validation
3. Semantic lowering to Xian IR
4. IR validation and normalization
5. Bytecode generation
6. Bytecode validation
7. VM execution against host state and context

### Phase 1: Source Parse

- Contract source is parsed into Python AST using a pinned supported frontend
  parser.
- Parsing is a build step only.
- Parse success alone does not imply the contract is valid Xian code.

### Phase 2: Source Validation

The validator enforces the Xian contract subset:

- allowed statements
- allowed expressions
- allowed declarations
- allowed imports
- allowed builtins
- static structural limits

Any construct outside the supported subset must fail before IR generation.

### Phase 3: Semantic Lowering To Xian IR

The frontend lowers validated Python AST into Xian IR.

Xian IR is where consensus semantics become explicit:

- variable scopes
- call boundaries
- control flow
- storage effects
- event emission
- context reads
- arithmetic semantics
- decimal semantics
- exception semantics

### Phase 4: Bytecode Generation

Xian IR compiles into versioned bytecode.

Bytecode is:

- stable within a bytecode version
- independent of CPython opcode layout
- designed for deterministic execution and direct metering

### Phase 5: VM Execution

The Xian VM:

- loads bytecode
- creates a call frame
- executes instructions
- issues host syscalls when required
- charges stamps per instruction and syscall
- returns a deterministic result or revert

## Language Boundary

The Xian contract language is a restricted Python-like language, not full
Python.

### Allowed Categories

The first VM-compatible language subset should include:

- module-level state declarations supported by Xian
- function definitions
- explicit decorators supported by Xian
- local variables
- integer, decimal, boolean, string, bytes, `None`
- lists and dictionaries only if their runtime semantics are explicitly defined
- arithmetic and comparison operators
- boolean operators
- `if` / `elif` / `else`
- bounded `for` loops over explicitly supported iterables
- `while` only if explicitly retained by the subset policy
- explicit contract-to-contract calls
- explicit event emission
- explicit state access through Xian constructs

### Disallowed Categories

The VM-target language must reject:

- unrestricted reflection
- dynamic attribute mutation beyond defined semantics
- dynamic import
- arbitrary module import
- arbitrary object construction
- Python metaclasses and metaprogramming hooks
- generators and coroutines unless explicitly designed into the VM
- threads, multiprocessing, async runtime primitives
- direct filesystem, network, subprocess, or OS access
- dependence on CPython-specific behavior such as descriptor edge cases that are
  not part of the Xian language contract

### Contract Language Is Owned By Xian

If a valid CPython program conflicts with Xian semantics, Xian semantics win.

The source language should be documented as:

- Python-inspired
- Python-authored
- Xian-defined

It must not be described as unrestricted Python execution.

## Machine Model

The first VM is a stack machine.

### Why A Stack Machine

The first version should optimize for simplicity, auditability, and explicit
metering rather than maximal theoretical performance.

A stack machine is the better first choice because:

- instruction semantics are compact and easy to specify
- operand movement is explicit
- implementation is simpler than a register allocator-driven VM
- it is easier to audit and test deterministically

This does not prevent a later internal rewrite or JIT strategy as long as the
observable machine contract remains unchanged.

### Execution State

Each call frame contains:

- bytecode pointer
- operand stack
- local variable slots
- exception/revert state
- caller context metadata
- signer context metadata
- contract id

Each execution instance contains:

- current frame stack
- remaining stamp budget
- host interface handle
- execution engine version
- gas schedule version

### Deterministic Limits

The VM must enforce explicit limits for:

- maximum call depth
- maximum operand stack depth
- maximum local slot count
- maximum collection sizes where relevant
- maximum return payload size

These limits are consensus policy and must be versioned.

## Value Model

The VM value model is Xian-defined and must not depend on Python object
behavior.

### Canonical Runtime Value Types

The first stable value set should include:

- `int`
- `decimal`
- `bool`
- `str`
- `bytes`
- `none`
- `datetime`
- `timedelta` only if its semantics are explicitly required and defined
- `list`
- `dict`

If `list` and `dict` are retained, their semantics must be explicitly defined:

- supported key/value types
- iteration order
- copy behavior
- mutation cost model
- encoding rules

### Integer Semantics

- Integers are arbitrary-precision signed integers unless Xian chooses a
  bounded range explicitly.
- Overflow behavior must be defined by Xian, not inherited from Python.

### Decimal Semantics

Decimals use the Xian decimal policy already defined by the runtime-types layer:

- fixed Xian-defined precision and range
- explicit overflow failure
- explicit rounding/truncation rules

The VM must reproduce those rules exactly.

### String And Bytes Semantics

- Strings are Unicode values with explicit canonical encoding rules where
  serialization is required.
- Bytes are raw byte arrays with explicit host-serialization rules.

### Equality And Ordering

- Equality is defined only for supported comparable type pairs.
- Ordering comparisons across unrelated types must fail deterministically.
- Truthiness is Xian-defined, not Python-inherited by accident.

## Storage Model

The VM does not own persistent blockchain state directly.

Persistent state access happens through host syscalls.

### State Rules

- Reads and writes are explicit host interactions.
- Persistent writes are not applied until transaction commit semantics allow
  them.
- speculative or transactional buffering belongs to the host execution engine,
  not to contract source semantics.

### Storage Keys

Storage keys remain Xian-defined external identifiers.

The VM does not expose low-level database internals to contracts.

## Host Syscalls

All non-pure effects are explicit host syscalls.

The first syscall families should include:

- `state_read`
- `state_write`
- `state_delete`
- `emit_event`
- `call_contract`
- `get_ctx_signer`
- `get_ctx_caller`
- `get_contract_name`
- `get_chain_id`
- `get_block_time`
- `get_block_height`
- `get_block_hash` if exposed by Xian semantics
- `hash_*` helpers
- approved cryptographic verification helpers

### Syscall Rules

- Syscalls are part of the execution contract.
- Syscalls are versioned.
- Syscalls are metered explicitly.
- Syscalls may fail only through documented deterministic error conditions.
- Syscalls must not expose host nondeterminism.

### Context Syscalls

Contract-visible context must be provided explicitly by the host:

- `ctx.signer`
- `ctx.caller`
- contract identity
- block time
- block height
- chain id

This preserves the current contract model while removing dependence on Python
runtime globals.

## Contract Calls

Cross-contract calls are VM-level calls mediated by the host.

### Semantics

- `ctx.signer` remains the original external transaction authorizer.
- `ctx.caller` becomes the immediate calling contract on cross-contract calls.
- `ctx.caller` restores on frame unwind.
- call-depth limit is explicit and enforced by the VM.
- failure semantics are deterministic and versioned.

### Call Boundary

Each contract call creates a new frame with:

- its own local slots
- its own operand stack
- inherited signer
- updated caller
- the callee contract identity

## Events

Event emission is a host syscall.

The VM defines:

- argument evaluation order
- event name handling
- event payload value constraints
- serialization behavior

Event persistence and indexing remain host responsibilities.

## Error And Revert Semantics

The VM must distinguish at least these classes:

- successful return
- contract-level revert
- deterministic runtime error
- host syscall failure
- stamp exhaustion
- invalid bytecode or invalid execution state

### Required Rules

- stamp exhaustion always aborts execution deterministically
- invalid host access always aborts execution deterministically
- overflow and illegal type operations fail explicitly
- revert behavior must specify which state changes and emitted events are
  discarded
- error payloads visible to callers must be canonical and versioned

## Metering Model

Metering is defined directly on the Xian machine.

### What Gets Charged

The gas schedule must cover:

- VM instruction execution
- host syscalls
- storage key/value byte effects where applicable
- event payload size where applicable
- return payload size
- explicit expensive helpers such as crypto operations

### What Does Not Get Charged Indirectly

The VM model must not depend on:

- CPython line events
- CPython opcode tables
- Python tracing callbacks
- Python object allocation side effects as consensus behavior

### Schedule Versioning

Gas schedules are versioned independently from source code.

Suggested network execution policy shape:

```yaml
execution:
  engine:
    mode: xian_vm_v1
    bytecode_version: xvm-1
    gas_schedule: xvm-gas-1
```

All validators on a network must use the same execution engine mode and gas
schedule when those choices affect consensus or stamps.

## Determinism Rules

The VM must satisfy:

- same bytecode
- same input payload
- same prior state
- same block context
- same network execution policy

must always produce:

- the same result
- the same state writes
- the same event set
- the same stamp usage

### Explicit Determinism Constraints

The VM must not permit:

- local wall-clock time
- host filesystem access
- host network access
- environment variable reads from contract code
- nondeterministic iteration order
- floating-point behavior inherited from host language runtimes

## Compilation Artifacts

Compiled contract artifacts should carry:

- source hash
- language subset version
- IR version
- bytecode version
- gas schedule target or compatibility marker
- optional debug/source map

### Source Maps

Debugging support should preserve a source map from source spans to IR/bytecode
regions.

This is for:

- error reporting
- developer tooling
- non-consensus debug output

Source maps must not affect execution semantics.

## Bytecode Validation

The VM must validate bytecode before execution.

Validation must reject:

- unknown opcodes
- malformed instruction operands
- invalid jump targets
- invalid stack effects
- invalid local-slot access
- invalid syscall identifiers
- invalid constant pool references

Execution must never rely on undefined behavior for malformed bytecode.

## Network Policy Surface

The execution engine becomes an explicit network policy decision.

Suggested long-term config shape:

```yaml
execution:
  engine:
    mode: python_line_v1
```

or

```yaml
execution:
  engine:
    mode: native_instruction_v1
```

or

```yaml
execution:
  engine:
    mode: xian_vm_v1
    bytecode_version: xvm-1
    gas_schedule: xvm-gas-1
```

### Rules

- no silent fallback between engines
- validators on one network must agree on engine mode when it changes
  consensus-relevant semantics
- upgrades between engines or bytecode versions must be explicit network policy

## Compatibility And Migration

The VM should not replace the current engine abruptly.

### Recommended Rollout

1. Keep current CPython-backed execution as the default stable engine.
2. Define the Xian language subset more formally where needed.
3. Implement Xian IR and bytecode generation.
4. Implement a Rust VM prototype.
5. Run contracts in shadow mode for parity testing.
6. Build a deterministic parity suite covering:
   - state writes
   - events
   - `ctx.signer` / `ctx.caller`
   - return values
   - decimal semantics
   - error behavior
   - stamp usage
7. Add `xian_vm_v1` as an optional network engine only after parity and
   workload confidence are strong.

### Existing Contracts

Existing source contracts should be recompiled into VM artifacts under the new
engine.

There should be no attempt to execute old CPython bytecode inside the VM.

### Migration Policy

- migration must be explicit
- engine version must be visible in network policy
- contract compilation target must be explicit
- mixed-engine execution in one network should be avoided unless the behavior is
  fully specified

## Implementation Phases

### Phase 1: Spec Freeze

- freeze the language subset required for `xian_vm_v1`
- freeze the value model
- freeze syscall semantics
- freeze error classes
- freeze gas schedule principles

### Phase 2: IR And Compiler Prototype

- lower current valid subset into Xian IR
- prove stable semantic lowering for representative contracts
- define source maps

### Phase 3: VM Prototype

- implement stack machine in Rust
- implement instruction dispatch
- implement host syscall interface
- implement direct metering

### Phase 4: Parity Harness

- run existing contracts through both engines
- compare outputs, writes, events, and errors
- build contract corpus and workload scenarios

### Phase 5: Optional Network Rollout

- add node configuration for `xian_vm_v1`
- add manifest support
- add tooling and docs
- deploy only as opt-in execution policy first

## Risks

- The engineering scope is large.
- The language subset may require tighter definition than current contracts
  assume.
- Collection and object semantics can become a source of hidden complexity if
  not constrained early.
- Tooling, debugging, and source maps must stay good enough that contract
  authors do not lose the ergonomics benefit of Python syntax.
- A partial VM with unclear boundaries would be worse than the current model.

## Explicit Rejections

This design rejects:

- directly executing CPython bytecode as the long-term VM format
- defining gas semantics in terms of CPython internals
- treating arbitrary Python runtime behavior as consensus behavior
- reusing the tracer abstraction as the permanent long-term execution model

## Open Questions

These questions should be resolved before implementation freezes `xian_vm_v1`:

- Should the first VM expose both `list` and `dict`, or should one or both be
  narrowed initially?
- Should `while` loops remain in the first VM-target subset, or should the
  language favor more statically inspectable iteration first?
- Should the first VM execute bytecode directly, or should it interpret Xian IR
  first and introduce bytecode only once the IR stabilizes?
- Should cryptographic helpers live as generic host syscalls, or as
  scheme-specific syscalls with tighter semantics?

These are design questions, not implementation freedom. They should be resolved
explicitly before the engine is declared stable.
