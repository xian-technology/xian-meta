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
- `XIAN_VM_FOUNDATION_BASELINE.md`: current implementation baseline for the VM-front-end subset, explicit execution-policy config shape, structural IR lowering, explicit runtime host ops, first Rust-side VM crate, and authored-contract audit status
- `XIAN_VM_LANGUAGE_EXPANSION_ROADMAP.md`: ranked roadmap for growing the contract language safely now that Xian owns its VM semantics instead of inheriting CPython's execution boundary
- `XIAN_VM_PARALLEL_EXECUTION_PLAN.md`: concrete plan for replacing the current speculative process-pool parallel executor with a deterministic, access-spec-driven design that is actually worth enabling by default
- `COMETBFT_TO_SEI_MIGRATION_MEMO.md`: evaluation of what a move from CometBFT to Sei's integrated chain stack would actually mean for Xian and why it is not a drop-in swap
- `XIAN_MISSION_AND_PRODUCT_STRATEGY.md`: shared mission, principles, and product direction for Xian
- `XIAN_X402_EXACT_PROFILE.md`: first native-Xian x402 exact-payment profile for HTTP 402 paid API requests
- `GOLDEN_PATH_ROADMAP.md`: phased cross-repo implementation roadmap for the product thesis
- `EXAMPLES.md`: canonical definition of the reference example set and first example scope
- `LOCALNET_E2E_RUNBOOK.md`: current cross-repo pointer for the 5-validator localnet and release-safety validation flows
- `PYPI_RELEASE_ROLLOUT.md`: one-time PyPI Trusted Publishing registration map, release order, and maintainer checklist for the Python package set
- `XIAN_SECURITY_AUDIT_FOLLOWUPS.md`: status note for the latest stack-wide security audit, including fixed findings and the remaining dashboard/simulation follow-up decisions
- `SHARED_FOUNDATIONS_PLAN.md`: cleanup plan for neutral shared Python foundations and removing the `xian-abci -> xian-py` dependency
- `SHARED_PACKAGE_EXTRACTION_PLAN.md`: deferred extraction criteria and migration path for shared packages that currently live in `xian-contracting`
- `INTENTKIT_STACK_INTEGRATION.md`: cross-repo contract for keeping `xian-intentkit` independent while attaching it cleanly to the stack and CLI
- `DETERMINISTIC_RANDOMNESS.md`: design for a Xian-owned deterministic contract randomness model and simulation alignment
- `REAL_PRIVACY_TOKEN_ARCHITECTURE.md`: architecture for replacing the current experimental privacy-token contract with a real shielded-note token backed by native proof verification
- `PRIVATE_SUBMISSION_RELAYER_ARCHITECTURE.md`: current network-layer relayer service, discovery shape, and trust boundary for proof-bound private submission
- `PRIVACY_ASSET_STACK_FOLLOW_UPS.md`: deferred cross-repo gap list for what still remains before the shielded-note stack can be treated as fully finished
- `PRIVACY_ASSET_THREAT_MODEL.md`: first explicit threat-model and privacy-review pass for the current shielded asset stack
- `SHIELDED_RELAYER_OPERATOR_RUNBOOK.md`: baseline operating posture, auth/rate-limit policy, retention guidance, metrics, and manifest publication rules for relayer operators
- `SHIELDED_WALLET_RECOVERY_MODEL.md`: current operational recovery model for shielded wallets, including BDS history requirements, wallet `state_snapshot` backups, and snapshot-based recovery expectations
- `ZK_VERIFIER_RUNTIME.md`: runtime design for a native Groth16/BN254 verifier bridge, key registry, encoding rules, and metering
