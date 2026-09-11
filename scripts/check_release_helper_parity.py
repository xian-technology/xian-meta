#!/usr/bin/env python3
"""Reject drift between the self-contained Python package release helpers."""

import argparse
from pathlib import Path

HELPERS = ("xian-py/scripts/release_context.py", "xian-linter/scripts/release_context.py")


def check(workspace: Path) -> list[str]:
    missing = [name for name in HELPERS if not (workspace / name).is_file()]
    if missing:
        return [f"Missing release helper: {name}" for name in missing]
    if (workspace / HELPERS[0]).read_bytes() != (workspace / HELPERS[1]).read_bytes():
        return [f"Release helpers differ: {HELPERS[0]} and {HELPERS[1]}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    errors = check(args.workspace_root)
    for error in errors:
        print(error)
    if not errors:
        print("Python release helpers match")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
