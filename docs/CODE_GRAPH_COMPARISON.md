# Graphify and GitNexus on Xian

Evaluated 2026-09-11. Recommendation: keep Graphify as the default after the
workflow improvements. GitNexus provides useful diff-to-symbol navigation,
but this test found no caller-recall advantage and exposed a stale-deletion
case in its normal analysis path.

## Method

- Graphify 0.9.58 with full structural refreshes and directed graphs.
- GitNexus 1.6.11, CLI `analyze --index-only --workers 2`, local parsers,
  default call-graph analysis; embeddings and PDG disabled.
- Separate local clones of the same three source revisions. No application
  code changes in the user's working checkouts.
- Twelve source-reviewed cases, containing 28 expected caller-to-callee
  relationships. Python named-call inventories were cross-checked with the
  standard-library AST; TypeScript, Rust and native-binding expectations were
  checked at the recorded source lines.
- Graphify `affected --relation calls --depth 1` versus GitNexus `context`
  incoming calls with a 1,000-result limit. Exact target file/ID selection.
- Score unique caller symbols within each fixture's declared production-source
  scope. Exclude tests. Repeated calls by one symbol count once. This measures
  caller inventory quality, not semantic search or all-language accuracy.

| Repository | Commit |
| --- | --- |
| xian-abci | `7463024a79459519903488dee3181e991eeeb232` |
| xian-contracting | `77c12f918bd725a01b747c5e72c0eb9d4ef1d104` |
| xian-js | `3343df5345b1bee4ecb5efa989367f4c1011d418` |

The reference cases live in `tests/fixtures/code_graph_cases.json`; each has
target identity, expected callers, source call-site lines and scope. The
runner checks the pinned revisions and rejects tracked working-tree changes.

## Caller Results

| Case family | Expected relationships | Graphify found | GitNexus found |
| --- | ---: | ---: | ---: |
| Python ABCI query helpers, 3 cases | 7 | 7 | 7 |
| Python compiler helpers, 3 cases | 8 | 8 | 8 |
| TypeScript local/cross-file signing helpers, 2 cases | 7 | 7 | 7 |
| TypeScript package re-export, 1 case | 3 | 0 | 0 |
| Rust submission-name helpers, 2 cases | 2 | 2 | 2 |
| Python-to-Rust binding, 1 case | 1 | 0 | 0 |
| **Total** | **28** | **24** | **24** |

Both passed 10 of 12 cases, with no unexpected callers within the tested
scopes. The 24/28 result is an 85.7% recall measurement on this deliberately
small diagnostic sample, not an estimate for the whole workspace.

Both missed these boundaries:

- `createXianMessageSigningPayload` in `@xian-tech/types` is called by
  `signXianMessage`, `verifyXianMessage`, and the provider's `request` method
  through package exports. Both returned an empty caller list for the source
  definition. Installing the SDK dependencies with `npm ci --ignore-scripts`,
  building the SDK with `npm run build`, and rebuilding both indexes did not
  recover those three source-definition edges.
- The Python compiler wrapper's `_lower_source_to_ir_json` alias enters the
  Rust `lower_source_to_ir_json_py` function through a PyO3 exported name.
  Neither tool connected that call to the Rust implementation.

## Cross-Repo Check

Three ABCI production sites instantiate `ContractingClient`: `Xian.__init__`
in `src/xian/xian_abci.py:157`, the client construction in
`_get_worker_runtime` in `src/xian/parallel_executor.py:70`, and `main` in
`src/xian/simulator_worker.py:22`.

Graphify's `merge-graphs` view did not connect those sites to the contracting
repo's class. GitNexus group synchronization produced zero contracts/links
for these repos, both with its default detection settings and with
`detect.workspace_deps: true`. Its group impact query returned no cross-repo
hits. These three missed cross-repo relationships are separate from the
28-relationship table above.

GitNexus's Python workspace extractor derives import names from distribution
names by replacing hyphens with underscores; `xian-tech-contracting` versus
`contracting` is a relevant mismatch. Neither tool should replace source
search at Xian's package, native-binding or network boundaries.

## Freshness and Real-Change Checks

In the isolated ABCI clone, add an untracked module that imports
`_bounded_int_param` and calls it from `code_graph_comparison_probe`. Keep HEAD
unchanged. Refresh, query the caller inventory, delete the file, then refresh
and query again.

| Check | Graphify with workspace helper | GitNexus |
| --- | --- | --- |
| Detect new untracked caller as stale | Pass | Pass (`status`) |
| Find caller after normal refresh | Pass | Pass |
| Detect deleted caller as stale | Pass | Pass (`status`) |
| Remove caller after normal refresh | Pass | **Fail: `analyze` said “Already up to date”** |
| Remove caller after forced rebuild | Not needed | Pass (`analyze --force`) |

The GitNexus deletion result applies specifically to deleting the newly
indexed untracked file and returning the working tree to its committed
content without changing HEAD. It does not establish that every deletion
fails. A forced rebuild removed the stale caller.

For the real contracting change at `77c12f9`, GitNexus `detect-changes
--scope compare --base-ref HEAD~1` correctly named `is_valid_submission_name`
and `contract_name_is_formatted`. It reported zero affected processes and
low risk. Graphify's three-hop reverse-call query reached
`is_valid_submission_name`, `validate_transaction_static_impl`, and
`decode_and_validate_transaction_static`. Treat process counts and risk
labels as heuristics; zero processes did not mean there were no callers.

GitNexus also reported process-enumeration truncation while indexing ABCI.
The caller test uses symbol relationships rather than that truncated flow
list. Build/query times were recorded but are not a controlled performance
benchmark: work overlapped and caches/dependency initialization differed.

## Reproduce

Use disposable sibling clones at the revisions above. Install the specified
tool versions, preserving any Graphify extras needed for the languages.
Set `EVAL_ROOT` to an absolute scratch directory containing `repos/` with
those three clones, and `GITNEXUS_BIN` to the installed GitNexus executable.
Use a separate registry so the comparison does not alter normal MCP setup.

```bash
export GITNEXUS_HOME="$EVAL_ROOT/gitnexus-home"
for repo in xian-abci xian-contracting xian-js; do
  python3 scripts/graphify_workspace.py refresh \
    --workspace-root "$EVAL_ROOT/repos" --repo "$repo"
  "$GITNEXUS_BIN" analyze "$EVAL_ROOT/repos/$repo" \
    --index-only --name "$repo-test" --workers 2
done
python3 scripts/benchmark_code_graphs.py \
  --repos "$EVAL_ROOT/repos" --gitnexus "$GITNEXUS_BIN" \
  --gitnexus-home "$GITNEXUS_HOME" --out "$EVAL_ROOT/results"
```

The runner saves raw stdout/stderr and structured `results.json`. The local
evaluation evidence, including refresh reproduction script, build logs,
group outputs, real-diff output and caller results, is retained under
`graphify-out/comparison-2026-09-11/` in this checkout (generated, uncommitted).

## Adopted Workflow

The workspace uses directed local Graphify graphs with source-content and
graph-digest freshness stamps, `affected` for dependency questions, source
verification at returned locations, and explicit sibling-repo searches.
The helper preserves the existing semantic layer but does not claim to
refresh its LLM interpretations. See `CODE_GRAPH_WORKFLOW.md`.

GitNexus remains an isolated evaluation installation. No global GitNexus
editor setup, hooks, or replacement of Graphify was performed. Reconsider it
if it demonstrably resolves the missing boundaries or supplies a needed
workflow advantage; this test does not justify a workspace-wide migration.
