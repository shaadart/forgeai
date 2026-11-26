"""forge build | resume | chat | doctor"""

import argparse
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

import yaml

from . import chat, pipeline
from .index import Embedder
from .llm import LLM, LLMError, load_config, load_env


def _llm(config: dict, run_dir: Path, args) -> LLM:
    return LLM(config, run_dir / "llm_calls.jsonl", args.budget_tokens, args.replay)


def _run(run_dir: Path, settings: dict, args) -> int:
    config = load_config(Path(settings["config"]) if settings["config"] else None)
    try:
        return pipeline.build(
            run_dir, settings["brief"], Path(settings["docs"]), _llm(config, run_dir, args),
            Embedder(config["embeddings"]["model"]), settings["unattended"], settings["answers"],
            settings["max_refits"])
    except KeyboardInterrupt:
        print(f"\ninterrupted. Continue with: forge resume {run_dir}")
        return pipeline.CRASHED
    except LLMError as e:
        print(f"\nmodel call failed: {str(e)[:300]}\nContinue with: forge resume {run_dir}")
        return pipeline.CRASHED
    except Exception:
        traceback.print_exc()
        print(f"\na stage crashed. Continue with: forge resume {run_dir}")
        return pipeline.CRASHED


def build(args) -> int:
    brief = Path(args.brief).read_text().strip()
    if not brief or not Path(args.docs).is_dir():
        print("--brief must be a non-empty text file and --docs a folder")
        return 1
    slug = "-".join(re.findall(r"[a-z0-9]+", brief.lower())[:5])
    run_dir = Path(args.out) / (args.run_id or f"{time.strftime('%Y%m%d-%H%M%S')}-{slug}")
    if (run_dir / "run.json").exists():
        print(f"{run_dir} already holds a run. Use: forge resume {run_dir}")
        return 1
    settings = {
        "brief": brief, "docs": str(Path(args.docs).resolve()), "unattended": args.unattended,
        "answers": yaml.safe_load(Path(args.answers).read_text()) if args.answers else None,
        "max_refits": args.max_refits, "config": str(Path(args.config).resolve()) if args.config else None}
    run_dir.mkdir(parents=True, exist_ok=True)
    pipeline.save(run_dir / "run.json", settings)
    print(f"run folder: {run_dir}")
    return _run(run_dir, settings, args)


def resume(args) -> int:
    run_dir = Path(args.run_dir)
    settings = json.loads((run_dir / "run.json").read_text())
    if args.config:
        settings["config"] = args.config
    # finished stages replay from the call cache, so they cost nothing
    return _run(run_dir, settings, args)


def talk(args) -> int:
    config = load_config(Path(args.config) if args.config else None)
    return chat.chat(Path(args.agent), LLM(config), Embedder(config["embeddings"]["model"]), args.reindex)


def doctor(args) -> int:
    config = load_config(Path(args.config) if args.config else None)
    failures = 0

    def report(name, ok, detail=""):
        nonlocal failures
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name} {detail}")

    families = {side: re.split(r"[-:\d]", config[side]["model"].split("/")[-1].lower())[0]
                for side in ("builder", "examiner")}
    report("model families differ", families["builder"] != families["examiner"], str(families))
    report("token budget set", config.get("limits", {}).get("budget_tokens", 0) > 0)
    for side in ("builder", "examiner"):
        key = config[side]["api_key_env"]
        report(f"{side} key", bool(os.environ.get(key)), key)
        try:
            text = LLM(config).chat(side, [{"role": "user", "content": 'Reply with this JSON: {"ok": true}'}])
            report(f"{side} reachable", "ok" in text, config[side]["model"])
        except Exception as e:
            report(f"{side} reachable", False, str(e)[:300])
    try:
        Embedder(config["embeddings"]["model"])(["hello"])
        report("embedding model", True, config["embeddings"]["model"])
    except Exception as e:
        report("embedding model", False, str(e)[:300])
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> None:
    load_env()
    parser = argparse.ArgumentParser(prog="forge", description="Builds a document-grounded agent and tests it.")
    commands = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="path to a forge.toml")
    running = argparse.ArgumentParser(add_help=False, parents=[common])
    running.add_argument("--budget-tokens", type=int, help="stop early and still write the report")
    running.add_argument("--replay", action="store_true", help="serve model calls from the cache only")

    p = commands.add_parser("build", parents=[running], help="build, test, refit, report")
    p.add_argument("--brief", required=True, help="text file with the one-paragraph brief")
    p.add_argument("--docs", required=True, help="folder of documents")
    p.add_argument("--unattended", action="store_true", help="no prompts; defaults are recorded as ASSUMED")
    p.add_argument("--answers", help="yaml mapping question ids (Q1...) to answers")
    p.add_argument("--max-refits", type=int, default=3, choices=range(4))
    p.add_argument("--out", default="runs")
    p.add_argument("--run-id")
    p.set_defaults(handler=build)

    p = commands.add_parser("resume", parents=[running], help="continue a run")
    p.add_argument("run_dir")
    p.set_defaults(handler=resume)

    p = commands.add_parser("chat", parents=[common], help="talk to a built agent")
    p.add_argument("agent", help="path to an agent yaml")
    p.add_argument("--reindex", action="store_true", help="accept changed documents")
    p.set_defaults(handler=talk)

    p = commands.add_parser("doctor", parents=[common], help="check keys, models and embeddings")
    p.set_defaults(handler=doctor)

    args = parser.parse_args(argv)
    try:
        sys.exit(args.handler(args))
    except FileNotFoundError as e:  # a mistyped path is a user error, not a crash
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
