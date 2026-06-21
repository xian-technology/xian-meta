#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_sha(repo_path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def git_ref(repo_path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    ).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report resolved sibling repository SHAs for CI failure triage."
    )
    parser.add_argument(
        "--workspace-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Directory containing the sibling repos",
    )
    parser.add_argument(
        "--manifest",
        default=str(Path(__file__).resolve().parents[1] / "workspace-repos.json"),
        help="Path to workspace-repos.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(args.workspace_root).resolve()
    manifest = load_manifest(Path(args.manifest).resolve())

    lines = [
        "## Resolved Workspace SHAs",
        "",
        "| Repo | Tier | Ref | SHA |",
        "| --- | --- | --- | --- |",
    ]
    for repo in manifest.get("repos", []):
        name = repo["name"]
        if repo.get("tier") == "exempt":
            continue
        repo_path = workspace_root / name
        if not (repo_path / ".git").exists():
            lines.append(f"| `{name}` | {repo.get('tier', 'light')} | missing | missing |")
            continue
        lines.append(
            f"| `{name}` | {repo.get('tier', 'light')} | `{git_ref(repo_path)}` | `{git_sha(repo_path)}` |"
        )

    report = "\n".join(lines) + "\n"
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(report)
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
