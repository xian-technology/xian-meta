import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "parity", Path(__file__).resolve().parents[1] / "scripts/check_release_helper_parity.py"
)
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


class ReleaseHelperParityTests(unittest.TestCase):
    def test_missing_helpers_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(len(parity.check(Path(directory))), 2)

    def test_exact_copies_pass_and_drift_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in parity.HELPERS:
                path = root / name
                path.parent.mkdir(parents=True)
                path.write_bytes(b"# release helper\n")
            self.assertEqual(parity.check(root), [])
            (root / parity.HELPERS[1]).write_bytes(b"# different release helper\n")
            self.assertEqual(len(parity.check(root)), 1)
