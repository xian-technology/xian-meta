#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_url(organization: str, repo: dict) -> str:
    if "url" in repo:
        return repo["url"]
    slug = repo.get("slug") or repo["name"]
    return f"https://github.com/{organization}/{slug}.git"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone missing Xian sibling repos into the expected workspace layout."
    )
    parser.add_argument(
        "--workspace-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Directory that should contain the sibling repos",
    )
    parser.add_argument(
        "--manifest",
        default=str(Path(__file__).resolve().parents[1] / "workspace-repos.json"),
        help="Path to workspace-repos.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print clone commands without running them",
    )
    parser.add_argument(
        "--include-exempt",
        action="store_true",
        help="Include exempt repos such as forked upstream integrations",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(args.workspace_root).resolve()
    manifest = load_manifest(Path(args.manifest).resolve())
    organization = manifest["organization"]

    workspace_root.mkdir(parents=True, exist_ok=True)

    for repo in manifest.get("repos", []):
        name = repo["name"]
        if repo.get("tier") == "exempt" and not args.include_exempt:
            print(f"skip {name}: exempt")
            continue
        if not repo.get("clone_by_default", True) and not args.include_exempt:
            print(f"skip {name}: clone_by_default=false")
            continue

        target = workspace_root / name
        if target.exists():
            print(f"ok   {name}: already exists")
            continue

        command = ["git", "clone", repo_url(organization, repo), str(target)]
        if args.dry_run:
            print("dry  " + " ".join(command))
            continue

        print(f"clone {name}")
        subprocess.run(command, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
