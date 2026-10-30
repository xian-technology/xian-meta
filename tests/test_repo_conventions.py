from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "check_repo_conventions",
    Path(__file__).absolute().parents[1] / "scripts/check_repo_conventions.py",
)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class OptionalCheckoutTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.repo = {"name": "xian-optional", "tier": "full", "clone_by_default": False}
        self.other_repos = []

    def check(self, *arguments):
        manifest = self.workspace / "manifest.json"
        manifest.write_text(json.dumps({"repos": [self.repo, *self.other_repos]}))
        argv = [
            "check", "--workspace-root", str(self.workspace),
            "--manifest", str(manifest), *arguments,
        ]
        output = io.StringIO()
        with (
            patch("sys.argv", argv),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(output),
        ):
            result = checker.main()
        return result, output.getvalue()

    def test_absent_optional_checkout_is_not_required(self):
        self.assertEqual(self.check()[0], 0)

    def test_explicit_optional_checkout_is_required(self):
        result, output = self.check("--repo", "xian-optional")
        self.assertEqual(result, 1)
        self.assertIn("repo path is missing", output)

    def test_present_optional_checkout_gets_full_tier_validation(self):
        (self.workspace / self.repo["name"]).mkdir()
        result, output = self.check()
        self.assertEqual(result, 1)
        self.assertIn("missing docs/ARCHITECTURE.md", output)

    def test_default_full_checkout_remains_required(self):
        del self.repo["clone_by_default"]
        self.assertEqual(self.check()[0], 1)

    def test_explicit_default_clone_policy_remains_required(self):
        self.repo["clone_by_default"] = True
        self.assertEqual(self.check()[0], 1)

    def test_optional_checkout_stays_optional_with_require_light(self):
        self.assertEqual(self.check("--require-light")[0], 0)

    def test_default_light_checkout_requires_explicit_gate(self):
        self.repo.update(tier="light", clone_by_default=True)
        self.assertEqual(self.check()[0], 0)
        self.assertEqual(self.check("--require-light")[0], 1)

    def test_allow_missing_overrides_explicit_selection(self):
        result, _ = self.check(
            "--repo", "xian-optional", "--allow-missing", "xian-optional"
        )
        self.assertEqual(result, 0)

    def test_valid_optional_checkout_passes(self):
        root = self.workspace / self.repo["name"]
        files = ("README.md", "AGENTS.md", "docs/ARCHITECTURE.md", "docs/BACKLOG.md")
        for relative in files:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("## Validation\n\n## Related Docs\n")
        self.assertEqual(self.check()[0], 0)

    def test_unknown_selection_is_rejected(self):
        result, output = self.check("--repo", "unknown")
        self.assertEqual(result, 1)
        self.assertIn("not declared in the manifest", output)

    def test_exempt_checkout_is_not_required(self):
        self.repo.update(tier="exempt", clone_by_default=True)
        self.assertEqual(self.check()[0], 0)

    def test_selection_does_not_require_unselected_checkout(self):
        self.other_repos = [{"name": "unselected", "tier": "full"}]
        result, _ = self.check(
            "--repo", "xian-optional", "--allow-missing", "xian-optional"
        )
        self.assertEqual(result, 0)
