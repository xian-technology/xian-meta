#!/usr/bin/env python3
"""Check and refresh the local structural graphs for the sibling workspace."""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


META = Path(__file__).resolve().parents[1]
STAMP = "xian-freshness.json"


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def source_state(repo: Path) -> dict:
    """Hash working files, including uncommitted edits, additions and deletions.

    Ignore generated indexes. Hash all other Git-visible files conservatively;
    this is an input freshness check, not a claim of parser coverage.
    """
    names = set(
        git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split(
            b"\0"
        )
    )
    digest = hashlib.sha256()
    count = 0
    for raw in sorted(names - {b""}):
        rel = os.fsdecode(raw)
        if rel.split("/", 1)[0] in {"graphify-out", ".gitnexus"}:
            continue
        path = repo / rel
        if path.is_symlink():
            content = b"symlink:" + os.fsencode(os.readlink(path))
        elif path.is_file():
            content = path.read_bytes()
        else:
            content = b"missing"
        digest.update(raw + b"\0" + hashlib.sha256(content).digest())
        count += 1
    return {
        "head": git(repo, "rev-parse", "HEAD").decode().strip(),
        "files": count,
        "sha256": digest.hexdigest(),
    }


def graph_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def graphify_version() -> str:
    executable = shutil.which("graphify")
    if not executable:
        return "unavailable"
    return (
        subprocess.check_output(
            [executable, "--version"], text=True, stderr=subprocess.DEVNULL
        )
        .strip()
        .removeprefix("graphify ")
    )


def status(repo: Path) -> list[str]:
    out = repo / "graphify-out"
    path = out / "graph.json"
    if not path.exists():
        return ["missing graph"]
    graph = json.loads(path.read_text())
    reasons = []
    if not graph.get("directed"):
        reasons.append("undirected")
    stamp_path = out / STAMP
    if not stamp_path.exists():
        reasons.append("no verified input stamp")
    else:
        stamp = json.loads(stamp_path.read_text())
        if stamp.get("graphify_version") != graphify_version():
            reasons.append("Graphify version changed")
        if stamp.get("source") != source_state(repo):
            reasons.append("source changed")
        if stamp.get("graph_sha256") != graph_hash(path):
            reasons.append("graph changed since verification")
    return reasons


def write_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def refresh(repo: Path, *, force: bool) -> None:
    # These adapters are isolated here because graphify's update CLI preserves
    # an existing directed flag but does not expose a direction option itself.
    import importlib.metadata
    from graphify.watch import _rebuild_code, _rebuild_lock

    out = repo / "graphify-out"
    out.mkdir(exist_ok=True)
    path = out / "graph.json"
    with _rebuild_lock(out, blocking=True) as acquired:
        if not acquired:
            raise RuntimeError("could not acquire graphify rebuild lock")
        before = source_state(repo)
        original = path.read_bytes() if path.exists() else None
        graph = (
            json.loads(original) if original is not None else {"nodes": [], "links": []}
        )
        if original is not None and not graph.get("directed"):
            backup = out / "graph.before-xian-directed.json"
            if not backup.exists():
                backup.write_bytes(original)
        try:
            # Re-extract every structural source: changing this flag alone
            # cannot recover reciprocal edges lost by an undirected build.
            graph["directed"] = True
            write_json(path, graph)
            if not _rebuild_code(repo, force=force, acquire_lock=False):
                raise RuntimeError("Graphify refused or failed the refresh")
            after = source_state(repo)
            if before != after:
                raise RuntimeError(
                    "sources changed during refresh; retry when edits settle"
                )
            current = json.loads(path.read_text())
            if not current.get("directed"):
                raise RuntimeError("Graphify did not preserve directed edges")
            # A topology-preserving refresh may retain an older upstream SHA.
            # The source digest above verifies the actual working tree too.
            current["built_at_commit"] = after["head"]
            write_json(path, current)
            write_json(
                out / STAMP,
                {
                    "schema_version": 1,
                    "source": after,
                    "graph_sha256": graph_hash(path),
                    "graphify_version": importlib.metadata.version("graphifyy"),
                    "scope": "structural; preserved semantic content is not re-extracted",
                },
            )
        except BaseException:
            if original is None:
                path.unlink(missing_ok=True)
            else:
                tmp = out / "graph.rollback.tmp"
                tmp.write_bytes(original)
                tmp.replace(path)
            (out / STAMP).unlink(missing_ok=True)
            raise


def graphify_python() -> str:
    executable = shutil.which("graphify")
    if not executable:
        raise RuntimeError("graphify is not installed or is not on PATH")
    first_line = Path(executable).read_text().splitlines()[0]
    interpreter = first_line.removeprefix("#!").strip()
    if not first_line.startswith("#!") or not Path(interpreter).is_file():
        raise RuntimeError(
            "cannot resolve Graphify's Python; use its Python interpreter directly"
        )
    return interpreter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "refresh"))
    parser.add_argument("--workspace-root", type=Path, default=META.parent)
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="refresh even when the input stamp is current",
    )
    parser.add_argument(
        "--force", action="store_true", help="accept intentional graph shrinkage"
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    manifest = json.loads((META / "workspace-repos.json").read_text())
    allowed = {r["name"] for r in manifest["repos"] if r["tier"] != "exempt"}
    if set(args.repo) - allowed:
        parser.error(
            "unknown or exempt repo: " + ", ".join(sorted(set(args.repo) - allowed))
        )
    repos = [args.workspace_root.resolve() / n for n in sorted(args.repo or allowed)]
    failed = False
    for repo in repos:
        if not repo.is_dir():
            if args.repo:
                print(f"{repo.name}: missing checkout", file=sys.stderr)
                failed = True
            continue
        try:
            reasons = status(repo)
            if args.command == "refresh" and (reasons or args.force or args.rebuild):
                if args.worker:
                    refresh(repo, force=args.force)
                else:
                    cmd = [
                        graphify_python(),
                        str(Path(__file__).resolve()),
                        "refresh",
                        "--workspace-root",
                        str(args.workspace_root.resolve()),
                        "--repo",
                        repo.name,
                        "--worker",
                    ]
                    if args.force:
                        cmd.append("--force")
                    if args.rebuild:
                        cmd.append("--rebuild")
                    subprocess.run(cmd, check=True, cwd=repo)
                reasons = status(repo)
            print(
                f"{repo.name}: {', '.join(reasons) if reasons else 'current, directed'}",
                flush=True,
            )
            failed |= bool(reasons)
        except (
            OSError,
            ValueError,
            RuntimeError,
            subprocess.CalledProcessError,
        ) as exc:
            print(f"{repo.name}: {exc}", file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
