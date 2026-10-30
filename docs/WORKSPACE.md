# Xian Workspace

This is the durable front door for the sibling-repo Xian workspace.

The workspace model is intentionally a set of independent Git repositories in
one parent directory, not a monorepo. Keep the directory names stable because
local file dependencies, CI jobs, documentation links, and cross-repo validation
all assume the sibling layout.

## Expected Layout

```text
.../xian/
  xian-meta/
  xian-abci/
  xian-contracting/
  xian-py/
  xian-js/
  xian-stack/
  ...
```

`workspace-repos.json` is the source of truth for the current repo list,
convention tier, default clone policy, and explicit exemptions.

To inspect or recreate the layout:

```bash
cd xian-meta
python3 ./scripts/bootstrap_workspace.py --workspace-root .. --dry-run
python3 ./scripts/check_repo_conventions.py --workspace-root ..
python3 ./scripts/report_workspace_shas.py --workspace-root ..
```

The bootstrap script only clones missing repos. It does not pull, reset, or
rewrite existing checkouts.

## Optional Migration Tooling

`xian-migration` owns offline legacy-state migration analysis and rehearsal.
It is full-tier because it handles state conversion, but `clone_by_default` is
`false`: ordinary node, SDK, and workspace development does not need it. Clone
it explicitly into the sibling layout when working on a migration:

```bash
git clone https://github.com/xian-technology/xian-migration.git ../xian-migration
python3 ./scripts/check_repo_conventions.py --workspace-root .. --repo xian-migration
```

These commands assume the current directory is `xian-meta`. Follow the migration
repo's README for its pinned dependencies and explicit network/contract inputs.
The dependency points one way: `xian-migration` consumes node/runtime tooling;
`xian-abci` does not import or depend on migration implementation. Its node
package, image, and normal startup do not require the migration checkout.

Default convention checks allow absent optional repos and validate them when
present. Selecting a repo with `--repo` requires its checkout unless explicitly
allowed through `--allow-missing`. Full-tier structural requirements apply to
the migration repo just as they do to other full-tier repos.

## Progressive Disclosure

Start with the narrowest page that matches the question, then follow links only
when the task needs more depth.

| Question | Start Here |
| --- | --- |
| What repos exist and how do I clone them? | `workspace-repos.json`, then this page |
| What must each repo expose at the root? | `docs/REPO_CONVENTIONS.md` |
| What should an agent read before editing a repo? | that repo's `AGENTS.md`, then the relevant README |
| What is the change discipline before push? | `docs/CHANGE_WORKFLOW.md` |
| How do I check graph freshness and find affected code? | `docs/CODE_GRAPH_WORKFLOW.md` |
| What is ready for a future public network launch? | `docs/MAINNET_LAUNCH_PLAN.md` |
| What is the compiler/runtime launch status? | `docs/COMPILER_RUNTIME_LAUNCH_STATUS.md` |
| What is the overall product direction? | `docs/XIAN_MISSION_AND_PRODUCT_STRATEGY.md` |
| What VM design documents exist? | `docs/XIAN_VM_EXECUTION_MODEL.md` and linked VM docs |

Repo-local files remain authoritative for repo-local behavior. Use
`xian-meta` for shared contracts and cross-repo orientation, then dive into the
owning repo for implementation details.

## Network Scope

The current codebase does not have an active public testnet or public mainnet.
Use local nodes, localnet, or the explicit draft mainnet launch manifest when
working with this codebase.

Do not add public chain IDs or public RPC endpoints to repo defaults until a
new launch manifest is final, rehearsed, and linked from
`docs/MAINNET_LAUNCH_PLAN.md`. The draft chain ID reserved for the new
current-codebase mainnet is `xian-mainnet-1`.

## Exemptions

Forked or upstream-shaped repos are declared as `exempt` in
`workspace-repos.json`. Do not apply shared Xian repo conventions to an exempt
repo unless a fork-specific change is deliberately requested.

## CI Reproducibility

Cross-repo CI may still check out sibling `main` branches for fresh integration
coverage during pull requests. Scheduled or manually dispatched cross-repo
smoke jobs should use pinned sibling SHAs unless an accepted launch manifest
defines a different set. Any workflow that checks out sibling repos should
report the resolved sibling SHAs using:

```bash
python3 ./scripts/report_workspace_shas.py --workspace-root ..
```

Those SHAs make failures bisectable without replacing the release path's pinned
manifests.
