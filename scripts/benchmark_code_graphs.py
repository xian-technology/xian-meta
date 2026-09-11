#!/usr/bin/env python3
"""Compare source-reviewed direct caller inventories from two existing indexes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time


def normalize(name: str) -> str:
    return name.removesuffix("()").lstrip(".").rsplit(".", 1)[-1]


def in_scope(file: str, prefixes: list[str]) -> bool:
    return any(file.startswith(p) for p in prefixes) and not any(
        part in {"tests", "test", "__tests__"} for part in Path(file).parts
    )


def run(cmd: list[str], env: dict, output: Path) -> tuple[str, float]:
    start = time.monotonic()
    result = subprocess.run(cmd, env=env, text=True, capture_output=True, check=True)
    seconds = time.monotonic() - start
    output.write_text(result.stdout)
    output.with_suffix(".stderr.txt").write_text(result.stderr)
    return result.stdout, seconds


def score(actual: set, expected: set) -> dict:
    return {
        "correct": sorted(actual & expected),
        "missed": sorted(expected - actual),
        "unexpected": sorted(actual - expected),
        "expected": len(expected),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repos", type=Path, required=True, help="isolated indexed sibling checkouts"
    )
    parser.add_argument("--gitnexus", required=True, help="GitNexus CLI executable")
    parser.add_argument("--gitnexus-home", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "tests/fixtures/code_graph_cases.json",
    )
    args = parser.parse_args()
    fixture = json.loads(args.cases.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GITNEXUS_HOME": str(args.gitnexus_home.resolve())}
    revisions = {}
    for repo, expected_sha in fixture["revisions"].items():
        sha = subprocess.check_output(
            ["git", "-C", str(args.repos / repo), "rev-parse", "HEAD"], text=True
        ).strip()
        if sha != expected_sha:
            raise RuntimeError(f"{repo}: fixture expects {expected_sha}, found {sha}")
        subprocess.run(
            ["git", "-C", str(args.repos / repo), "diff", "--exit-code", "HEAD"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        revisions[repo] = sha
    results = []
    for i, case in enumerate(fixture["cases"], 1):
        root = args.repos / case["repo"]
        graph_path = root / "graphify-out/graph.json"
        graph = json.loads(graph_path.read_text())
        candidates = [
            n
            for n in graph["nodes"]
            if n.get("source_file") == case["file"]
            and normalize(n.get("label", "")) == case["target"]
        ]
        if len(candidates) != 1:
            raise RuntimeError(
                f"{case['target']}: Graphify target missing or ambiguous: {candidates}"
            )
        prefix = args.out / f"{i:02d}-{case['target']}"
        text, graphify_seconds = run(
            [
                "graphify",
                "affected",
                candidates[0]["id"],
                "--relation",
                "calls",
                "--depth",
                "1",
                "--graph",
                str(graph_path),
            ],
            env,
            prefix.with_suffix(".graphify.txt"),
        )
        graphify_callers = set()
        for line in text.splitlines():
            match = re.match(r"^- (.+?) \[calls\] (.+?):L\d+", line)
            if match and in_scope(match[2], case["scope"]):
                graphify_callers.add((match[2], normalize(match[1])))
        text, gitnexus_seconds = run(
            [
                args.gitnexus,
                "context",
                case["target"],
                "--file",
                case["file"],
                "--repo",
                case["repo"] + "-test",
                "--limit",
                "1000",
            ],
            env,
            prefix.with_suffix(".gitnexus.txt"),
        )
        result = json.loads(text[text.index("{") :])
        if result.get("status") != "found":
            raise RuntimeError(
                f"{case['target']}: GitNexus did not resolve target: {result}"
            )
        gitnexus_callers = {
            (n["filePath"], normalize(n["name"]))
            for n in result.get("incoming", {}).get("calls", [])
            if in_scope(n["filePath"], case["scope"])
        }
        expected = {(n["file"], n["name"]) for n in case["expected"]}
        row = {
            "case": case,
            "graphify": score(graphify_callers, expected),
            "gitnexus": score(gitnexus_callers, expected),
            "cli_seconds": {"graphify": graphify_seconds, "gitnexus": gitnexus_seconds},
        }
        results.append(row)
        print(
            case["target"],
            {
                tool: {
                    "correct": len(row[tool]["correct"]),
                    "missed": len(row[tool]["missed"]),
                    "unexpected": len(row[tool]["unexpected"]),
                }
                for tool in ("graphify", "gitnexus")
            },
            flush=True,
        )
    (args.out / "results.json").write_text(
        json.dumps({"revisions": revisions, "results": results}, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
