import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "rust_parity", Path(__file__).resolve().parents[1] / "scripts/check_rust_toolchain_parity.py"
)
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)

IMAGE = "ARG RUST_IMAGE=rust:1.100.0-bookworm@sha256:abc\n"


def workspace(root: Path, image: str, workflow: str) -> Path:
    dockerfile = root / parity.DOCKERFILE
    dockerfile.parent.mkdir(parents=True)
    dockerfile.write_text(image)
    workflows = root / parity.WORKFLOWS
    workflows.mkdir(parents=True)
    (workflows / "validate.yml").write_text(workflow)
    return root


class RustToolchainParityTests(unittest.TestCase):
    def test_missing_files_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(len(parity.check(Path(directory))), 1)

    def test_matching_pins_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            workflow = "uses: dtolnay/rust-toolchain@1.100.0\nrust-toolchain: 1.100.0\n"
            self.assertEqual(parity.check(workspace(Path(directory), IMAGE, workflow)), [])

    def test_floating_or_different_pins_fail(self):
        for workflow in ("uses: dtolnay/rust-toolchain@stable\n", "rust-toolchain: 1.99.0\n"):
            with tempfile.TemporaryDirectory() as directory:
                root = workspace(Path(directory), IMAGE, workflow)
                self.assertEqual(len(parity.check(root)), 1)

    def test_unpinned_workflows_and_image_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = workspace(Path(directory), IMAGE, "run: cargo test\n")
            self.assertEqual(len(parity.check(root)), 1)
        with tempfile.TemporaryDirectory() as directory:
            root = workspace(Path(directory), "ARG RUST_IMAGE=rust:latest\n", "")
            self.assertEqual(len(parity.check(root)), 1)


if __name__ == "__main__":
    unittest.main()
