import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


# Keep the test in the mutator's symlink overlay.
SCRIPT = Path(__file__).absolute().parents[1] / "scripts/bootstrap_workspace.py"


class BootstrapWorkspaceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.workspace = root / "nested" / "workspace"
        self.origin = root / "origin.git"
        self.manifest = root / "repos.json"
        self.manifest.write_text(json.dumps({
            "organization": "example",
            "repos": [
                {"name": "default-repo", "tier": "full"},
                {"name": "optional-repo", "tier": "full", "clone_by_default": False},
                {"name": "exempt-fork", "tier": "exempt", "clone_by_default": False},
            ],
        }))

    def run_bootstrap(self, *flags):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--workspace-root", str(self.workspace),
             "--manifest", str(self.manifest), *flags],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def test_dry_run_prints_command_without_creating_workspace(self):
        output = self.run_bootstrap("--dry-run")
        self.assertIn(
            "dry  git clone https://github.com/example/default-repo.git", output
        )
        self.assertIn("skip exempt-fork: exempt", output)
        self.assertFalse(self.workspace.exists())

    def test_include_exempt_keeps_optional_non_exempt_repos_excluded(self):
        output = self.run_bootstrap("--dry-run", "--include-exempt")
        self.assertIn("dry  git clone https://github.com/example/exempt-fork.git", output)
        self.assertIn("skip optional-repo: clone_by_default=false", output)

    def test_bootstrap_clones_missing_repository_under_new_workspace(self):
        subprocess.run(["git", "init", "--bare", "--quiet", str(self.origin)], check=True)
        manifest = json.loads(self.manifest.read_text())
        manifest["repos"][0]["url"] = str(self.origin)
        self.manifest.write_text(json.dumps(manifest))

        self.assertIn("clone default-repo", self.run_bootstrap())
        self.assertTrue((self.workspace / "default-repo" / ".git").is_dir())
        self.assertIn("ok   default-repo: already exists", self.run_bootstrap())
