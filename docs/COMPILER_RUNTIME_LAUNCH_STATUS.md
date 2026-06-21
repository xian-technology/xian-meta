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
- Deployment is artifact-backed: source-only on-node compilation is not the
  current path.
- The Rust compiler core builds `xian_contract_artifact_v1` artifacts through
  the `contracting.artifacts` surface used by Python tooling.
- Browser/Node and CLI consumers have native compiler integration paths.
- The VM baseline has moved past pure validation: native execution covers a
  bounded but real `xian_ir_v1` subset, deployment artifact validation, native
  deployment staging, runtime metrics, and localnet E2E coverage.
- Canonical source-to-runtime recompilation is still not a single fully
  Rust-owned public boundary across every consumer and validation mode.

## Launch Gates

Treat the compiler/runtime migration as launch-ready only when:

- one compiler authority is declared for the public launch train
- Python, JS/WASM, CLI, and IDE artifact outputs are fixture-identical for the
  accepted corpus
- rejected contracts produce stable diagnostics across public compiler surfaces
- node-side artifact validation accepts artifacts from every public compiler
  binding
- five-node E2E, localnet release checks, and VM runtime metrics pass from the
  pinned release manifest
- docs, SDK examples, and product defaults all describe artifact-backed
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
