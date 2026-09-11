# Code Graph Workflow

Use Graphify as a source-navigation aid for the sibling workspace. An absent
edge is not proof that no dependency exists, especially across Python package
boundaries, native bindings, runtime contract imports, or RPC calls.

## Check Freshness

From an owning repo, check its graph before relying on dependency results:

```bash
python3 ../xian-meta/scripts/graphify_workspace.py status --repo xian-abci
```

Replace `xian-abci` with the owning repo. Omit `--repo` to check all present,
non-exempt repos. Exit code 1 means at least one graph needs attention. The
check compares the commit, working-file contents (including uncommitted edits,
additions and deletions), graph digest, and directed flag. A matching commit
alone is insufficient. Graphify version changes invalidate the stamp too.
Ignored build outputs are excluded. Rebuild deliberately after changing an
ignored dependency installation or its generated exports; the stamp does
not fingerprint the entire dependency environment. Use `refresh --rebuild`
to bypass only the freshness shortcut while retaining the shrink guard.

## Refresh Structural Content

```bash
python3 ../xian-meta/scripts/graphify_workspace.py refresh --repo xian-abci
```

The helper uses the installed Graphify Python environment. It rebuilds code
and other supported structural inputs locally without an LLM, preserves
existing semantic content, and uses Graphify's rebuild lock and shrink guard.
The first directed migration saves `graph.before-xian-directed.json` locally
and re-extracts sources to recover reciprocal calls; relabeling an old graph
as directed would not recover those edges. Updates preserve directed mode.

Use `--force` only after inspecting an intentional deletion or refactor that
causes the shrink guard to refuse a refresh. A failed refresh restores the
prior graph and leaves it unverified. Concurrent source edits also prevent a
freshness stamp. The helper adapts Graphify's Python update API; validate it
after changing the installed Graphify version.

The stamp verifies input freshness, not complete parser coverage or refreshed
LLM interpretations. Changed semantic docs, PDFs and media still need the
Graphify skill's semantic update. Read their source if the semantic layer is
not current. Graph reports and HTML are generated navigation artifacts.

## Choose the Query

```bash
graphify query "contract admission" --budget 1500
graphify explain "ContractingClient"
graphify affected "ContractingClient" --depth 1
graphify affected "ContractingClient" --depth 3
graphify path "caller" "callee" --directed
```

- `query` finds context and explores connections; it is not a complete caller
  inventory. Expand wording with actual graph labels when a query misses.
- `explain` shows a symbol's immediate relationships. Disambiguate repeated
  labels by graph node ID or source location.
- `affected` traverses dependencies in reverse. Depth 1 gives immediate
  dependents; larger depths include transitive impact. Use `--relation calls`
  when the question is specifically about callers.
- Directed `path` follows dependency direction. Use `--undirected` only when
  asking how concepts are connected, not what calls what.

Inspect the returned source locations before making a change. Check the
corresponding sibling repos separately: a local graph does not automatically
provide a complete workspace-wide call graph. Follow imports, package
manifests, native interfaces and API consumers with source search when needed.
Never interpret a truncated response as a complete dependency list.

Refresh changed repos before final verification and repeat the relevant
impact queries. Keep `graphify-out/` and its stamps/backups uncommitted.

## Helper Validation

```bash
python3 -m unittest discover -s tests -p 'test_graphify_workspace.py'
python3 scripts/check_repo_conventions.py --workspace-root ..
```
