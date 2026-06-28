#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_README_MARKERS = (
    "## Validation",
    "## Related Docs",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_manifest(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def check_repo(repo_root: Path, repo_entry: dict, *, require_missing: bool) -> list[str]:
    errors: list[str] = []
    repo_name = repo_entry["name"]
    repo = repo_root / repo_name

    if not repo.exists():
        return [f"{repo_name}: repo path is missing"] if require_missing else []

    for rel in ("README.md", "AGENTS.md"):
        if not (repo / rel).exists():
            errors.append(f"{repo_name}: missing {rel}")

    tier = repo_entry.get("tier", "light")
    if tier == "full":
        docs_dir = repo_entry.get("docs_dir", "docs")
        internal_required = (f"{docs_dir}/ARCHITECTURE.md", f"{docs_dir}/BACKLOG.md")

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


def check_repo_with_missing_allowlist(
    repo_root: Path,
    repo_entry: dict,
    *,
    require_missing: bool,
    allow_missing: set[str],
) -> list[str]:
    repo_name = repo_entry["name"]
    repo = repo_root / repo_name

    if not repo.exists() and repo_name in allow_missing:
        print(f"{repo_name}: missing repo path allowed by --allow-missing")
        return []

    return check_repo(repo_root, repo_entry, require_missing=require_missing)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the shared xian-meta repo-structure conventions."
    )
    parser.add_argument(
        "--workspace-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Path that contains the sibling xian-* repos",
    )
    parser.add_argument(
        "--manifest",
        default=str(Path(__file__).resolve().parents[1] / "workspace-repos.json"),
        help="Path to workspace-repos.json",
    )
    parser.add_argument(
        "--require-light",
        action="store_true",
        help="Treat missing light-tier repos as errors instead of validating only when present",
    )
    parser.add_argument(
        "--allow-missing",
        action="append",
        default=[],
        metavar="REPO",
        help="Allow a required repo path to be absent, for CI jobs without private-repo checkout access",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(args.workspace_root).resolve()
    manifest = load_manifest(Path(args.manifest).resolve())
    allow_missing = set(args.allow_missing)
    errors: list[str] = []

    for repo in manifest.get("repos", []):
        tier = repo.get("tier", "light")
        if tier == "exempt":
            continue
        require_missing = tier == "full" or args.require_light
        errors.extend(
            check_repo_with_missing_allowlist(
                workspace_root,
                repo,
                require_missing=require_missing,
                allow_missing=allow_missing,
            )
        )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("All checked repos match the shared root-structure conventions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
