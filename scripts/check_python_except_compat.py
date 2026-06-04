#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_REPOS = (
    "xian-abci",
    "xian-cli",
    "xian-configs",
    "xian-contracting",
    "xian-deploy",
    "xian-docs-web",
    "xian-intentkit",
    "xian-linter",
    "xian-py",
    "xian-stack",
)

SKIP_DIRS = {
    ".artifacts",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

UNPARENTHESIZED_MULTI_EXCEPT = re.compile(
    r"^(?P<indent>\s*)except\s+"
    r"(?P<types>[A-Za-z_][A-Za-z0-9_\.]*"
    r"(?:\s*,\s*[A-Za-z_][A-Za-z0-9_\.]*)+)"
    r"(?P<rest>\s*(?:as\s+[A-Za-z_][A-Za-z0-9_]*)?\s*:.*)$"
)


def iter_python_files(repo: Path):
    for path in repo.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def check_file(path: Path, workspace_root: Path) -> list[str]:
    errors: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = UNPARENTHESIZED_MULTI_EXCEPT.match(line)
        if match is None:
            continue
        exception_types = ", ".join(
            item.strip() for item in match.group("types").split(",")
        )
        fixed = (
            f"{match.group('indent')}except "
            f"({exception_types})"
            f"{match.group('rest')}"
        )
        rel_path = path.relative_to(workspace_root)
        errors.append(
            f"{rel_path}:{line_no}: use parenthesized multi-exception syntax: {fixed}"
        )
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reject Python 3.14-only unparenthesized multi-exception handlers."
        )
    )
    parser.add_argument(
        "--workspace-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Path that contains the sibling xian-* repos",
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        help="Repo name to check. Can be passed more than once.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(args.workspace_root).resolve()
    repo_names = tuple(args.repos or DEFAULT_REPOS)
    errors: list[str] = []

    for repo_name in repo_names:
        repo = workspace_root / repo_name
        if not repo.exists():
            errors.append(f"{repo_name}: repo path is missing")
            continue
        for path in iter_python_files(repo):
            errors.extend(check_file(path, workspace_root))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Python except syntax is compatible with Python 3.13 and earlier.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
