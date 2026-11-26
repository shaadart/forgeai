"""Factory runs started from the web UI: one detached `forge build` per run.

The UI never runs the pipeline itself, so a closed tab or a stopped UI can't stop a run.
Note: process checks read /proc, so this is Linux only. Use psutil if it must run elsewhere.
"""

import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from .inventory import SUPPORTED
from .llm import ROOT

PID, LOG = "ui.pid", "build.log"


def running(run_dir: Path) -> bool:
    try:
        pid = int((run_dir / PID).read_text())
        args = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")
    except (OSError, ValueError):
        return False
    # a finished process has an empty command line, and a reused pid doesn't name this run
    return "forge.cli" in args and (run_dir.name in args or str(run_dir.resolve()) in args)


def state(run_dir: Path) -> str:
    """finished | running | not_groundable | stopped | outside (no UI process to ask)."""
    if running(run_dir):
        return "running"
    if (run_dir / "scorecard.json").is_file():
        return "finished"
    if (run_dir / "report.md").is_file():
        return "not_groundable"
    return "stopped" if (run_dir / PID).is_file() else "outside"


def _spawn(run_dir: Path, args: list[str]) -> None:
    with (run_dir / LOG).open("a") as log:
        process = subprocess.Popen([sys.executable, "-u", "-m", "forge.cli", *args], cwd=ROOT, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    (run_dir / PID).write_text(str(process.pid))


def _only_one(root: Path) -> None:
    """Two builds at once fight over the same rate limit."""
    busy = [p.name for p in root.iterdir() if p.is_dir() and running(p)] if root.is_dir() else []
    if busy:
        raise ValueError(f"Run {busy[0]} is still going. Wait for it, or stop it on the Factory log tab.")


def start(root: Path, brief: str, files: list[str], config: Path) -> str:
    """Copy the documents into a new run folder and start building. Returns the run id."""
    root, brief = root.resolve(), (brief or "").strip()
    if not brief:
        raise ValueError("Write the brief first: one paragraph saying what the agent should do.")
    usable = [Path(f) for f in files or [] if Path(f).suffix.lower() in SUPPORTED]
    if not usable:
        raise ValueError(f"Add at least one document ({', '.join(SUPPORTED)}).")
    names = [f.name for f in usable]
    if len(set(names)) < len(names):
        raise ValueError("Two documents have the same file name. Rename one and add it again.")
    _only_one(root)
    slug = "-".join(re.findall(r"[a-z0-9]+", brief.lower())[:5])
    run_dir = root / f"{time.strftime('%Y%m%d-%H%M%S')}-{slug}"[:90]
    (run_dir / "docs").mkdir(parents=True)
    for f in usable:
        shutil.copyfile(f, run_dir / "docs" / f.name)
    (run_dir / "brief.txt").write_text(brief + "\n")
    _spawn(run_dir, ["build", "--brief", str(run_dir / "brief.txt"), "--docs", str(run_dir / "docs"), "--unattended",
                     "--config", str(config.resolve()), "--out", str(root), "--run-id", run_dir.name])
    return run_dir.name


def resume(run_dir: Path, config: Path) -> None:
    if not (run_dir / "run.json").is_file():
        raise ValueError("This run stopped before it saved its settings. Start a new one.")
    _only_one(run_dir.parent)
    _spawn(run_dir.resolve(), ["resume", str(run_dir.resolve()), "--config", str(config.resolve())])


def stop(run_dir: Path) -> None:
    if running(run_dir):  # finished stages and model calls are on disk, so resume loses nothing
        os.kill(int((run_dir / PID).read_text()), signal.SIGTERM)
