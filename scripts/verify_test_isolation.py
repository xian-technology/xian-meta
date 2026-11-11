#!/usr/bin/env python3
"""Verify independent pytest processes and test cases own their state directories."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import uuid
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import IO

REPOS = ("xian-abci", "xian-contracting")
PROBE = Path(__file__).with_name("isolation_probe.py")


@dataclass
class Worker:
    role: str
    process: subprocess.Popen
    channel: socket.socket
    reader: IO[str]
    output: Path

    def send(self, event: str) -> None:
        self.channel.sendall(json.dumps({"event": event}).encode() + b"\n")

    def expect(self, event: str) -> dict:
        line = self.reader.readline()
        if not line:
            self.process.wait(timeout=10)
            raise RuntimeError(
                f"{self.role} closed its barrier:\n{self.output.read_text()[-4000:]}"
            )
        message = json.loads(line)
        if message.get("event") != event:
            raise RuntimeError(f"{self.role}: expected {event}, received {message}")
        return message

    def finish(self, timeout: float) -> None:
        if self.process.wait(timeout=timeout):
            raise RuntimeError(
                f"{self.role} pytest failed:\n{self.output.read_text()[-4000:]}"
            )

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        self.reader.close()
        self.channel.close()


def start_worker(
    *,
    repo: Path,
    python: Path,
    probe: Path,
    mode: str,
    role: str,
    sandbox: Path,
    timeout: float,
) -> Worker:
    parent, child = socket.socketpair()
    parent.settimeout(timeout)
    output = sandbox / f"{role}.log"
    env = os.environ | {
        "HOME": str(sandbox / "bootstrap-home"),
        "TMPDIR": str(sandbox),
        "PYTHONDONTWRITEBYTECODE": "1",
        "XIAN_ISOLATION_REPO": repo.name,
        "XIAN_ISOLATION_MODE": mode,
        "XIAN_ISOLATION_ROLE": role,
        "XIAN_ISOLATION_FD": str(child.fileno()),
        "XIAN_ISOLATION_TIMEOUT": str(timeout),
        "XIAN_ISOLATION_TOKEN": uuid.uuid4().hex,
        "XIAN_ISOLATION_ROOTS": json.dumps([str(sandbox), str(repo / ".tmp-home")]),
    }
    command = [
        str(python),
        "-m",
        "pytest",
        "-q",
        "-s",
        "-o",
        f"cache_dir={sandbox / (role + '-cache')}",
        "--basetemp",
        str(sandbox / role),
        str(probe),
    ]
    try:
        with output.open("w") as log:
            process = subprocess.Popen(
                command,
                cwd=repo,
                env=env,
                pass_fds=(child.fileno(),),
                stdout=log,
                stderr=subprocess.STDOUT,
            )
    except BaseException:
        parent.close()
        raise
    finally:
        child.close()
    return Worker(role, process, parent, parent.makefile("r", encoding="utf-8"), output)


def coordinate(owner: Worker, resetter: Worker, timeout: float) -> list[dict]:
    locations = [owner.expect("ready")["paths"], resetter.expect("ready")["paths"]]
    resetter.send("reset")
    resetter.expect("reset_done")
    owner.send("check")
    owner.expect("survived")
    for worker in (owner, resetter):
        worker.send("finish")
    for worker in (owner, resetter):
        worker.finish(timeout)
    for name in ("home", "node_home", "storage_home"):
        if locations[0][name] == locations[1][name]:
            raise RuntimeError(f"Independent pytest processes shared {name}")
    return locations


def verify(repo: Path, python: Path, mode: str, timeout: float = 60) -> dict:
    with tempfile.TemporaryDirectory(prefix="xian-test-isolation-") as temp:
        sandbox = Path(temp)
        probe_dir = (
            repo / "tests" / "abci_methods"
            if mode == "node_fixture"
            else repo / "tests"
        )
        with tempfile.NamedTemporaryFile(
            prefix="isolation_probe_", suffix=".py", dir=probe_dir
        ) as probe_file:
            probe = Path(probe_file.name)
            shutil.copyfile(PROBE, probe)
            with ExitStack() as stack:
                workers = []
                for role in ("owner", "resetter"):
                    worker = start_worker(
                        repo=repo,
                        python=python,
                        probe=probe,
                        mode=mode,
                        role=role,
                        sandbox=sandbox,
                        timeout=timeout,
                    )
                    stack.callback(worker.close)
                    workers.append(worker)
                locations = coordinate(*workers, timeout)
    return {
        "repo": repo.name,
        "mode": mode,
        "ok": True,
        "processes": 2,
        "tests_per_process": 2,
        "locations": locations,
    }


def interpreter_overrides(values: list[str]) -> dict[str, Path]:
    result = {}
    for value in values:
        repo, separator, path = value.partition("=")
        if repo not in REPOS or not separator:
            raise ValueError("--python must be REPO=/absolute/path/to/python")
        result[repo] = Path(path).absolute()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--repo", choices=REPOS, action="append")
    parser.add_argument("--python", action="append", default=[], metavar="REPO=PATH")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument(
        "--defaults-only", action="store_true", help="Skip ABCI node_fixture probe."
    )
    args = parser.parse_args()
    if os.name != "posix":
        parser.error(
            "socket descriptor inheritance requires a supported POSIX node platform"
        )
    try:
        overrides = interpreter_overrides(args.python)
        results = []
        for name in args.repo or REPOS:
            repo = args.workspace_root.resolve() / name
            python = overrides.get(name, (repo / ".venv/bin/python").absolute())
            modes = ["defaults"]
            if name == "xian-abci" and not args.defaults_only:
                modes.append("node_fixture")
            for mode in modes:
                results.append(verify(repo, python, mode, args.timeout))
        print(json.dumps({"ok": True, "checks": results}, indent=2))
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"test isolation verification failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
