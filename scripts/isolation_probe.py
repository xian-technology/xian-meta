"""Disposable pytest probe used by verify_test_isolation.py."""

from __future__ import annotations

import json
import os
import shutil
import socket
from pathlib import Path

from contracting import constants
from contracting.storage.driver import Driver

_FIRST_PATHS: dict[str, str] = {}
_KEY = "con_isolation_probe.value"


def _paths() -> dict[str, str]:
    if os.environ["XIAN_ISOLATION_REPO"] == "xian-abci":
        from xian.constants import Constants

        node_home = Constants.COMETBFT_HOME
    else:
        node_home = Path.home() / ".cometbft"
    storage_home = constants.STORAGE_HOME
    paths = {"home": Path.home(), "node_home": node_home, "storage_home": storage_home}
    roots = [
        Path(value).resolve()
        for value in json.loads(os.environ["XIAN_ISOLATION_ROOTS"])
    ]
    for name, path in paths.items():
        assert any(path.resolve().is_relative_to(root) for root in roots), (
            f"Refusing to probe unsandboxed {name}: {path}"
        )
    return {name: str(path) for name, path in paths.items()}


def _use_node_fixture(request) -> None:
    if os.environ["XIAN_ISOLATION_MODE"] == "node_fixture":
        request.getfixturevalue("node_fixture")
        from xian.constants import Constants

        assert Constants.COMETBFT_GENESIS.is_file()


def _write_state(token: str, paths: dict[str, str]) -> None:
    with Driver() as driver:
        assert driver.storage_home == Path(paths["storage_home"])
        driver.set(_KEY, token)
        driver.commit()
    home = Path(paths["home"])
    node = Path(paths["node_home"])
    home.mkdir(parents=True, exist_ok=True)
    node.mkdir(parents=True, exist_ok=True)
    (home / "isolation-home-marker").write_text(token)
    (node / "isolation-node-marker").write_text(token)


def _check_state(token: str, paths: dict[str, str]) -> None:
    with Driver() as driver:
        assert driver.get(_KEY) == token, (
            "Another pytest process erased committed state"
        )
    assert (Path(paths["home"]) / "isolation-home-marker").read_text() == token
    assert (Path(paths["node_home"]) / "isolation-node-marker").read_text() == token


def _send(channel: socket.socket, event: str, **payload) -> None:
    channel.sendall(json.dumps({"event": event, **payload}).encode() + b"\n")


def _receive(reader, expected: str) -> None:
    message = reader.readline()
    assert message and json.loads(message)["event"] == expected, (expected, message)


def test_01_competing_lifecycles(request):
    _use_node_fixture(request)
    paths = _paths()
    _FIRST_PATHS.update(paths)
    token = os.environ["XIAN_ISOLATION_TOKEN"]
    with socket.socket(fileno=int(os.environ["XIAN_ISOLATION_FD"])) as channel:
        channel.settimeout(float(os.environ["XIAN_ISOLATION_TIMEOUT"]))
        with channel.makefile("r", encoding="utf-8") as reader:
            if os.environ["XIAN_ISOLATION_ROLE"] == "owner":
                _write_state(token, paths)
                _send(channel, "ready", paths=paths)
                _receive(reader, "check")
                _check_state(token, paths)
                _send(channel, "survived")
            else:
                _send(channel, "ready", paths=paths)
                _receive(reader, "reset")
                with Driver() as driver:
                    driver.flush_full()
                _write_state("resetter-" + token, paths)
                shutil.rmtree(Path(paths["node_home"]))
                _send(channel, "reset_done")
            _receive(reader, "finish")


def test_02_following_test_has_fresh_defaults(request):
    _use_node_fixture(request)
    paths = _paths()
    for name, previous in _FIRST_PATHS.items():
        assert paths[name] != previous, f"Following test reused {name}"
    with Driver() as driver:
        assert driver.get(_KEY) is None, "Previous test's committed value leaked"
    assert not (Path(paths["home"]) / "isolation-home-marker").exists()
    assert not (Path(paths["node_home"]) / "isolation-node-marker").exists()
