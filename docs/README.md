# Docs

This folder contains the shared repo-structure standard and stack-wide design
notes for the Xian workspace.

The scope here is intentionally narrow:

- shared conventions
- shared workflows
- cross-repo design contracts

Repo-local implementation notes and future-work details should stay in the
owning repo.

Files:

- `ARCHITECTURE.md`: what `xian-meta` owns and where its boundaries are
- `BACKLOG.md`: follow-up work for the standards repo itself
- `REPO_CONVENTIONS.md`: the common structure that the main repos should follow
- `CHANGE_WORKFLOW.md`: the common pre-push workflow for docs impact and validation
- `README_TEMPLATE.md`: the shared root README shape for the main repos
- `FOLDER_README_TEMPLATE.md`: the short per-folder entrypoint template
- `MULTI_ACCOUNT_SUPPORT.md`: protocol-level design for multi-scheme transaction accounts
- `XIAN_VM_EXECUTION_MODEL.md`: target design for a Xian-owned VM and bytecode execution model
- `XIAN_MISSION_AND_PRODUCT_STRATEGY.md`: shared mission, principles, and product direction for Xian
- `GOLDEN_PATH_ROADMAP.md`: phased cross-repo implementation roadmap for the product thesis
- `SOLUTION_PACKS.md`: canonical definition of the reference solution-pack set and the first pack scope
- `WHOLE_STACK_VALIDATION_PLAN.md`: resumable whole-stack validation and hardening plan
- `CORE_REPO_CLEANUP_PLAN.md`: staged cleanup plan for keeping the core repos human-first, minimal, and correctly layered
- `SHARED_FOUNDATIONS_PLAN.md`: cleanup plan for neutral shared Python foundations and removing the `xian-abci -> xian-py` dependency
- `SHARED_PACKAGE_EXTRACTION_PLAN.md`: deferred extraction criteria and migration path for shared packages that currently live in `xian-contracting`
- `CONTRACT_SOURCE_STORAGE.md`: design for storing exact submitted contract source alongside canonical runtime code
- `CONTRACT_FACTORY_DEPLOYMENT.md`: design for restoring contract factories with explicit constructor semantics, provenance, metering, and BDS indexing
- `DYNAMIC_CONTRACT_CALLS.md`: design for safe dynamic exported-function dispatch without exposing generic reflection
- `DETERMINISTIC_RANDOMNESS.md`: design for a Xian-owned deterministic contract randomness model and simulation alignment
- `REAL_PRIVACY_TOKEN_ARCHITECTURE.md`: architecture for replacing the current experimental privacy-token contract with a real shielded-note token backed by native proof verification
- `ZK_VERIFIER_RUNTIME.md`: runtime design for a native Groth16/BN254 verifier bridge, key registry, encoding rules, and metering
