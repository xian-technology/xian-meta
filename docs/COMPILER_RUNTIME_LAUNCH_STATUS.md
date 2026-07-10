# Compiler Runtime Launch Status

This page reconciles the compiler and VM launch status across the workspace.
Repo-local architecture docs remain useful, but this page is the current
cross-repo status reference before a public launch.

## Version State

- `xian-contracting` has a local `contracting-v1.0.11-beta.1` tag.
- `xian-stack` has progressed through `v0.1.0-beta.3`.
- `xian-py` has a local `v0.4.20-beta.1` tag.

These are beta/pre-release markers. They should not be presented as a stable
public launch train until the release manifest pins the exact versions and the
launch gates below are closed.

## Current Implementation State

- `xian_vm_v1` is the only supported execution-policy mode in the current node
  configuration.
- Deployment is source-backed: clients submit cleartext source, and validators
  compile and persist canonical IR on admission.
- The Rust compiler core builds `xian_contract_artifact_v1` artifacts through
  the `contracting.artifacts` surface used by Python tooling.
- Browser/Node and CLI consumers have native compiler integration paths.
- The VM baseline has moved past pure validation: native execution covers a
  bounded but real `xian_ir_v1` subset, source-backed native deployment,
  deployment staging, runtime metrics, and localnet E2E coverage.
- Canonical source-to-runtime compilation is the deployment admission boundary;
  offline artifact builders remain for diagnostics and CI.
- The Rust compiler core is authoritative for source-to-IR output and
  diagnostics across Python bindings, WASM/JavaScript, the standalone linter,
  and native node deployment admission. The legacy Python transformer remains
  local-harness-only.
- Compiler admission enforces identical deterministic bounds across those
  surfaces: 128 KiB source, 50,000 syntax nodes, depth 64, 100,000 tokens, and
  4,096 tokens per logical line.
- Accepted and rejected shared fixtures exercise byte-identical artifacts and
  stable diagnostics across Rust, Python, WASM/JavaScript, linter, and node
  admission.

## Closed Compiler Gates

- compiler authority is the Rust `xian-compiler-core`
- public bindings and node admission share canonical source/IR behavior
- rejected fixtures and compile-limit diagnostics are stable across the locally
  available public surfaces
- node-side deployment derives IR from source and rejects client-supplied IR
  artifacts

## Launch Gates

The compiler gates above do not make the runtime launch-ready by themselves.
The remaining launch gates are:

- five-node E2E, localnet release checks, and VM runtime metrics pass from the
  pinned release manifest
- docs, SDK examples, and product defaults all describe source-backed
  deployment consistently
- beta tags are promoted into an explicit release-candidate or stable launch
  versioning plan

## Related Source Docs

- `../xian-contracting/docs/RUST_COMPILER_CORE.md` defines the target compiler
  architecture and original authority gates.
- `XIAN_VM_FOUNDATION_BASELINE.md` records the implemented VM/runtime baseline
  and native-path progress.
- `LOCALNET_E2E_RUNBOOK.md` links the current five-validator localnet and
  release-safety validation flows.
