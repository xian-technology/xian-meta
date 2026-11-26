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

- [V2 numeric specification](NUMERIC_PROFILE_V2.md) defines exact arithmetic and interchange for fresh V2 networks.
- [Fresh-genesis contract language](FRESH_GENESIS_CONTRACT_LANGUAGE.md) defines the proposed source subset, numeric rules, application evidence and delivery gates.
- [CHAIN_EXECUTION_PROFILES_PLAN.md](CHAIN_EXECUTION_PROFILES_PLAN.md): proposed compiler/runtime extension contracts and delivery gates for new chains selecting their own language, costs and VM at genesis
- `ARCHITECTURE.md`: what `xian-meta` owns and where its boundaries are
- `BACKLOG.md`: follow-up work for the standards repo itself
- `WORKSPACE.md`: progressive-disclosure front door for the sibling repo layout
- `REPO_CONVENTIONS.md`: the common structure that the main repos should follow
- `OPERATIONAL_LOGGING.md`: shared record structure, diagnostic scope and retention ownership
- `CHANGE_WORKFLOW.md`: the common pre-push workflow for docs impact and validation
- `CODE_GRAPH_WORKFLOW.md`: local graph freshness, directed dependencies, and cross-repo verification
- `CODE_GRAPH_COMPARISON.md`: source-reviewed Graphify/GitNexus comparison and reproduction
- `CODEBASE_CONSISTENCY_AUDIT.md`: verified cross-repo protocol, dependency, signing, and bootstrap inconsistencies
- `TRANSACTION_ENCODING_CONTRACT.md`: canonical wire fixtures and shared runtime encoding requirements
- `MAINNET_LAUNCH_PLAN.md`: future public-network launch checklist for the current codebase
- [Oracle authorization V2](ORACLE_AUTHORIZATION_V2.md): proposed transaction-bound price authorization, exact stock-0.40 constraints and production gates for optional financial applications
- `COMPILER_RUNTIME_LAUNCH_STATUS.md`: reconciled compiler/runtime readiness status
- `README_TEMPLATE.md`: the shared root README shape for the main repos
- `FOLDER_README_TEMPLATE.md`: the short per-folder entrypoint template
- `MULTI_ACCOUNT_SUPPORT.md`: protocol-level design for multi-scheme transaction accounts
- `XIAN_VM_EXECUTION_MODEL.md`: original V1 execution model design record
- `XIAN_VM_FOUNDATION_BASELINE.md`: historical record of the first VM implementation slice
- `XIAN_VM_LANGUAGE_EXPANSION_ROADMAP.md`: ranked roadmap for growing the contract language safely around Xian-owned VM semantics instead of inheriting CPython's execution boundary
- `XIAN_SINGLE_ENGINE_PLAN.md`: migration record for the single Rust execution engine, including the approved decisions and proof gates
- [Transaction throughput optimization plan](TRANSACTION_THROUGHPUT_OPTIMIZATION_PLAN.md):
  proposed cross-repo admission reuse, queue handling, receipt optimization and
  measurement gates, with the
  [November 2026 baseline](TRANSACTION_THROUGHPUT_BASELINE_2026_11_19.json)
- `XIAN_VM_PARALLEL_EXECUTION_PLAN.md`: execution-speed roadmap (serial host speedups and a Rust block loop now, Block-STM threading deferred, with the measurements behind that order) and the deterministic, access-spec-driven design for any future parallel executor (the speculative process-pool executor was removed)
- `COMETBFT_TO_SEI_MIGRATION_MEMO.md`: evaluation of what a move from CometBFT to Sei's integrated chain stack would actually mean for Xian and why it is not a drop-in swap
- `XIAN_MISSION_AND_PRODUCT_STRATEGY.md`: shared mission, principles, and product direction for Xian
- `XIAN_X402_EXACT_PROFILE.md`: first native-Xian x402 exact-payment profile for HTTP 402 paid API requests
- `GOLDEN_PATH_ROADMAP.md`: phased cross-repo implementation roadmap for the product thesis
- `EXAMPLES.md`: canonical definition of the reference example set and first example scope
- `LOCALNET_E2E_RUNBOOK.md`: current cross-repo pointer for the 5-validator localnet and release-safety validation flows
- `VALIDATOR_OPERATIONS_RUNBOOK.md`: cross-repo acceptance evidence for validator onboarding, exit/unbond, jail/unjail, evidence/slashing, governance changes, and recovery rehearsals
- `PYPI_RELEASE_ROLLOUT.md`: March 2026 PyPI registration and rollout record
- `XIAN_SECURITY_AUDIT_FOLLOWUPS.md`: completed audit findings and scope for future security reviews
- `SHARED_FOUNDATIONS_PLAN.md`: implemented package boundaries for accounts and runtime types, and the decompiler retirement decision
- `SHARED_PACKAGE_EXTRACTION_PLAN.md`: deferred extraction criteria and migration path for shared packages that currently live in `xian-contracting`
- `INTENTKIT_STACK_INTEGRATION.md`: cross-repo contract for keeping `xian-intentkit` independent while attaching it cleanly to the stack and CLI
- `DETERMINISTIC_RANDOMNESS.md`: implemented deterministic VM randomness and its execution-context inputs
- `REAL_PRIVACY_TOKEN_ARCHITECTURE.md`: design record for the proof-backed shielded-note token
- `PRIVATE_SUBMISSION_RELAYER_ARCHITECTURE.md`: current network-layer relayer service, discovery shape, and trust boundary for proof-bound private submission
- `PRIVACY_ASSET_STACK_FOLLOW_UPS.md`: deferred cross-repo gap list for what still remains before the shielded-note stack can be treated as fully finished
- `PRIVACY_ASSET_THREAT_MODEL.md`: first explicit threat-model and privacy-review pass for the current shielded asset stack
- `SHIELDED_RELAYER_OPERATOR_RUNBOOK.md`: baseline operating posture, auth/rate-limit policy, retention guidance, metrics, and manifest publication rules for relayer operators
- `SHIELDED_WALLET_RECOVERY_MODEL.md`: current operational recovery model for shielded wallets, including BDS history requirements, wallet `state_snapshot` backups, and snapshot-based recovery expectations
- `ZK_VERIFIER_RUNTIME.md`: runtime design for a native Groth16/BN254 verifier bridge, key registry, encoding rules, and metering
