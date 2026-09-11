from __future__ import annotations

import contextlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "graphify_workspace",
    Path(__file__).resolve().parents[1] / "scripts/graphify_workspace.py",
)
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class GraphFreshnessTest(unittest.TestCase):
    def setUp(self):
        version = patch.object(workflow, "graphify_version", return_value="test")
        version.start()
        self.addCleanup(version.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "core.hooksPath", "/dev/null")
        (self.repo / ".gitignore").write_text("graphify-out/\n.gitnexus/\n")
        (self.repo / "example.py").write_text("def example():\n    return 1\n")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        )
        self.out = self.repo / "graphify-out"
        self.out.mkdir()
        self.graph = self.out / "graph.json"
        self.graph.write_text(json.dumps({"directed": True, "nodes": [], "links": []}))
        self.stamp()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args])

    def stamp(self):
        workflow.write_json(
            self.out / workflow.STAMP,
            {
                "source": workflow.source_state(self.repo),
                "graph_sha256": workflow.graph_hash(self.graph),
                "graphify_version": "test",
            },
        )

    def test_clean_graph_is_current(self):
        self.assertEqual(workflow.status(self.repo), [])

    def test_parser_upgrade_invalidates_stamp(self):
        with patch.object(workflow, "graphify_version", return_value="new"):
            self.assertIn("Graphify version changed", workflow.status(self.repo))

    def test_working_edit_without_commit_is_stale(self):
        (self.repo / "example.py").write_text("def example():\n    return 2\n")
        self.assertIn("source changed", workflow.status(self.repo))

    def test_added_and_deleted_files_are_stale(self):
        added = self.repo / "new.py"
        added.write_text("pass\n")
        self.assertIn("source changed", workflow.status(self.repo))
        added.unlink()
        self.assertEqual(workflow.status(self.repo), [])
        (self.repo / "example.py").unlink()
        self.assertIn("source changed", workflow.status(self.repo))

    def test_generated_outputs_do_not_stale_sources(self):
        (self.out / "graph.html").write_text("generated")
        (self.repo / ".gitnexus").mkdir()
        (self.repo / ".gitnexus/index").write_text("generated")
        self.assertEqual(workflow.status(self.repo), [])

    def test_external_graph_refresh_requires_verification(self):
        self.graph.write_text(json.dumps({"directed": False, "nodes": [], "links": []}))
        reasons = workflow.status(self.repo)
        self.assertIn("undirected", reasons)
        self.assertIn("graph changed since verification", reasons)

    def test_failed_rebuild_restores_prior_graph(self):
        original = self.graph.read_bytes()
        fake = types.ModuleType("graphify.watch")
        fake._rebuild_lock = lambda *a, **k: contextlib.nullcontext(True)
        fake._rebuild_code = lambda *a, **k: False
        with patch.dict(
            sys.modules,
            {"graphify": types.ModuleType("graphify"), "graphify.watch": fake},
        ):
            with self.assertRaisesRegex(RuntimeError, "failed"):
                workflow.refresh(self.repo, force=False)
        self.assertEqual(self.graph.read_bytes(), original)
        self.assertFalse((self.out / workflow.STAMP).exists())

    def test_concurrent_edit_does_not_receive_freshness_stamp(self):
        original = self.graph.read_bytes()
        fake = types.ModuleType("graphify.watch")
        fake._rebuild_lock = lambda *a, **k: contextlib.nullcontext(True)

        def change_source(*args, **kwargs):
            (self.repo / "example.py").write_text("# edited during extraction\n")
            return True

        fake._rebuild_code = change_source
        with patch.dict(
            sys.modules,
            {"graphify": types.ModuleType("graphify"), "graphify.watch": fake},
        ):
            with self.assertRaisesRegex(RuntimeError, "sources changed"):
                workflow.refresh(self.repo, force=False)
        self.assertEqual(self.graph.read_bytes(), original)
        self.assertFalse((self.out / workflow.STAMP).exists())


if __name__ == "__main__":
    unittest.main()
