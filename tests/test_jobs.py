"""The web UI's one door into the factory: a detached `forge build`."""

import time

import pytest

from forge import jobs
from forge.llm import ROOT

CONFIG = ROOT / "forge.toml"


def test_start_refuses_an_empty_brief_and_unsupported_files(tmp_path):
    exe = tmp_path / "tool.exe"
    exe.write_text("x")
    with pytest.raises(ValueError, match="brief"):
        jobs.start(tmp_path / "runs", "  ", [str(exe)], CONFIG)
    with pytest.raises(ValueError, match="at least one document"):
        jobs.start(tmp_path / "runs", "Answer questions.", [str(exe)], CONFIG)


def test_start_runs_the_real_cli_in_its_own_process(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("")  # unreadable, so the factory stops before its first model call
    runs = tmp_path / "runs"
    run = runs / jobs.start(runs, "Answer questions.", [str(empty)], CONFIG)
    deadline = time.monotonic() + 60
    while jobs.running(run) and time.monotonic() < deadline:
        time.sleep(0.2)
    assert jobs.state(run) == "not_groundable", (run / jobs.LOG).read_text()
    assert "no readable documents" in (run / jobs.LOG).read_text()
