#!/usr/bin/env python3
"""Reject drift between the Rust toolchain of the node image and contracting CI."""

import argparse
import re
from pathlib import Path

DOCKERFILE = "xian-stack/docker/xian-node.Dockerfile"
WORKFLOWS = "xian-contracting/.github/workflows"
IMAGE = re.compile(r"^ARG RUST_IMAGE=rust:(\d+\.\d+\.\d+)-", re.MULTILINE)
PIN = re.compile(r"(?:dtolnay/rust-toolchain@|rust-toolchain:\s*)(\S+)")


def check(workspace: Path) -> list[str]:
    dockerfile = workspace / DOCKERFILE
    workflows = sorted((workspace / WORKFLOWS).glob("*.yml"))
    if not dockerfile.is_file() or not workflows:
        return [f"Missing {DOCKERFILE} or {WORKFLOWS}"]
    image = IMAGE.search(dockerfile.read_text())
    if image is None:
        return [f"{DOCKERFILE} does not pin an exact rust image version"]
    pins = {path.name: PIN.findall(path.read_text()) for path in workflows}
    errors = [
        f"{WORKFLOWS}/{name} uses Rust {pin}, the node image uses {image.group(1)}"
        for name, found in pins.items()
        for pin in found
        if pin != image.group(1)
    ]
    if not any(pins.values()):
        errors.append(f"{WORKFLOWS} pins no Rust toolchain")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    errors = check(args.workspace_root)
    for error in errors:
        print(error)
    if not errors:
        print("Rust toolchain pins match the node image")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
