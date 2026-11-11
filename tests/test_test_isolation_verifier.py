"""The workspace verifier reports broken runtimes and cleans its child processes."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "verify_test_isolation", SCRIPTS / "verify_test_isolation.py"
)
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)


@unittest.skipUnless(os.name == "posix", "POSIX subprocess descriptors")
class IsolationVerifierFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="isolation-verifier-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "xian-abci"
        (self.repo / "tests").mkdir(parents=True)

    def executable(self, source):
        script = self.root / "python"
        script.write_text(f"#!{sys.executable}\n{source}")
        script.chmod(0o700)
        return script

    def assert_probe_removed(self):
        self.assertEqual(list((self.repo / "tests").iterdir()), [])

    def test_broken_pytest_runtime_reports_failure_and_removes_probe(self):
        python = self.executable(
            "import sys\nprint('pytest runtime unavailable', file=sys.stderr)\nraise SystemExit(9)\n"
        )
        with self.assertRaisesRegex(RuntimeError, "pytest runtime unavailable"):
            verifier.verify(self.repo, python, "defaults", timeout=3)
        self.assert_probe_removed()

    def test_late_pytest_failure_is_not_treated_as_success(self):
        python = self.executable(
            "import json, os, socket, sys\n"
            "channel = socket.socket(fileno=int(os.environ['XIAN_ISOLATION_FD']))\n"
            "reader = channel.makefile('r')\n"
            "role = os.environ['XIAN_ISOLATION_ROLE']\n"
            "def send(event, **payload):\n"
            "    channel.sendall(json.dumps({'event': event, **payload}).encode() + b'\\n')\n"
            "send('ready', paths={name: role + name for name in ['home', 'node_home', 'storage_home']})\n"
            "reader.readline()\n"
            "send('survived' if role == 'owner' else 'reset_done')\n"
            "reader.readline()\n"
            "print('following test leaked state', file=sys.stderr)\n"
            "raise SystemExit(9)\n"
        )
        with self.assertRaisesRegex(RuntimeError, "following test leaked state"):
            verifier.verify(self.repo, python, "defaults", timeout=3)
        self.assert_probe_removed()

    def test_stalled_worker_times_out_without_leaking_processes_or_probe(self):
        markers = self.root / "pids"
        markers.mkdir()
        python = self.executable(
            "import json, os, socket\n"
            "from pathlib import Path\n"
            "role = os.environ['XIAN_ISOLATION_ROLE']\n"
            "Path(os.environ['ISOLATION_TEST_PIDS'], role).write_text(str(os.getpid()))\n"
            "channel = socket.socket(fileno=int(os.environ['XIAN_ISOLATION_FD']))\n"
            "channel.sendall(json.dumps({'event': 'ready', 'paths': {}}).encode() + b'\\n')\n"
            "while channel.recv(1024):\n"
            "    pass\n"
        )
        with (
            patch.dict(os.environ, {"ISOLATION_TEST_PIDS": str(markers)}),
            self.assertRaises(TimeoutError),
        ):
            verifier.verify(self.repo, python, "defaults", timeout=1)
        self.assertEqual(len(list(markers.iterdir())), 2)
        for marker in markers.iterdir():
            with self.assertRaises(ProcessLookupError):
                os.kill(int(marker.read_text()), 0)
        self.assert_probe_removed()


if __name__ == "__main__":
    unittest.main()
