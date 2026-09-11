# Workspace Helper Tests

Run `python3 -m unittest discover -s tests` from `xian-meta` to validate the
graph freshness helper with temporary Git repositories.

`fixtures/code_graph_cases.json` contains source-reviewed caller inventories
for the code-graph comparison. Each case declares its production-source scope;
repeated call sites count once per caller. The pinned revisions prevent a
changed source tree from silently invalidating the reference answers. The
native-binding case deliberately tests a Python-to-Rust edge.

The comparison runner uses existing isolated indexes; it does not install
tools or edit code. See `docs/CODE_GRAPH_COMPARISON.md` for reproduction and
the limitations of this small diagnostic sample.
