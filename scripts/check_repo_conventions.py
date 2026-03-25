#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


MAIN_REPOS = (
    "xian-abci",
    "xian-cli",
    "xian-configs",
    "xian-contracting",
    "xian-deploy",
    "xian-docs-web",
    "xian-linter",
    "xian-meta",
    "xian-py",
    "xian-stack",
)

REQUIRED_README_MARKERS = (
    "## Validation",
    "## Related Docs",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_repo(repo_root: Path, repo_name: str) -> list[str]:
    errors: list[str] = []
    repo = repo_root / repo_name

    if not repo.exists():
        return [f"{repo_name}: repo path is missing"]

    for rel in ("README.md", "AGENTS.md"):
        if not (repo / rel).exists():
            errors.append(f"{repo_name}: missing {rel}")

    if repo_name == "xian-docs-web":
        internal_required = (".meta/ARCHITECTURE.md", ".meta/BACKLOG.md")
    else:
        internal_required = ("docs/ARCHITECTURE.md", "docs/BACKLOG.md")

    for rel in internal_required:
        if not (repo / rel).exists():
            errors.append(f"{repo_name}: missing {rel}")

    readme_path = repo / "README.md"
    if readme_path.exists():
        readme_text = read_text(readme_path)
        for marker in REQUIRED_README_MARKERS:
            if marker not in readme_text:
                errors.append(f"{repo_name}: README.md missing heading {marker}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the shared xian-meta repo-structure conventions."
    )
    parser.add_argument(
        "--workspace-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Path that contains the sibling xian-* repos",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(args.workspace_root).resolve()
    errors: list[str] = []

    for repo_name in MAIN_REPOS:
        errors.extend(check_repo(workspace_root, repo_name))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("All main repos match the shared root-structure conventions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
