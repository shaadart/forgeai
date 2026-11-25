"""Check the LLM judge against a person.

    uv run python judge_calibration/calibrate.py sheet   # writes sheet.md from the committed runs, judge verdicts hidden
    (fill in every "Label:" line with pass or fail)
    uv run python judge_calibration/calibrate.py score   # compares your labels with the judge

Only verdicts the model decided are sampled; code-decided failures are not the judge's work. Model calls are replayed
from the runs, so no model is needed. The spares judge failed a self-test; its labels are included to be measured.
"""

import json
import random
import re
import sys
from pathlib import Path

from forge import inventory, loop
from forge.index import Embedder, Index
from forge.llm import LLM, load_config
from forge.runtime import load_agent
from forge.schemas import Case

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "judge_calibration"
SHEET, KEY = HERE / "sheet.md", HERE / "judge_verdicts.json"
SIZE = 20


def decided() -> list[tuple]:
    config = load_config(ROOT / "forge.colab.toml")
    embed = Embedder(config["embeddings"]["model"])
    found = []
    for run, docs in (("mlc-crew-rights", "mlc"), ("spares-procurement", "spares")):
        folder, docs = ROOT / "runs" / run, ROOT / "data" / docs
        llm = LLM(config, folder / "llm_calls.jsonl", replay=True)
        cases = [Case.model_validate_json(x) for x in (folder / "evalset.jsonl").read_text().splitlines()]
        agent = load_agent(folder / "agent.v0.yaml")
        results = loop.run_cases(llm, agent, Index(inventory.scan(docs), embed, docs), cases, True)
        for case in cases:
            result = results[case.id]
            if result.state != "unknown" and not any(r.startswith("check ") for r in result.reasons):
                found.append((f"{run}/{case.id}", case, result))
    return found


def sheet() -> None:
    if SHEET.exists():
        sys.exit(f"{SHEET} exists. Delete it first; it may hold your labels.")
    found = decided()
    rng = random.Random(7)
    rng.shuffle(found)
    failed = [f for f in found if f[2].state == "failed"][: SIZE // 2]
    chosen = failed + [f for f in found if f[2].state == "passed"][: SIZE - len(failed)]
    rng.shuffle(chosen)
    parts = [
        "# Judge hand check", "",
        "Write `pass` or `fail` after each `Label:`. Do not open judge_verdicts.json first.", "",
        "**pass** needs both: every statement in the answer is backed by the evidence, and",
        "for `answer` all key facts are there; for `refuse` the reply declines;",
        "for `clarify` it asks which one is meant, or covers the key facts.", ""]
    for n, (name, case, result) in enumerate(chosen, 1):
        evidence = [c.text for c in result.turn.retrieved] + [c.result for c in result.turn.tool_calls if c.ok]
        parts += [f"## {n}. {name} (expected: {case.expected_behavior})", "", f"**Question:** {case.question}", "",
                  "**Key facts:** " + ("; ".join(f.fact for f in case.key_facts) or "none"), "",
                  f"**Reply ({result.turn.status}):** {result.turn.text}", "", "**Evidence:**", ""]
        parts += [f"> {' '.join(text.split())}\n" for text in evidence] + ["Label: ", ""]
    SHEET.write_text("\n".join(parts))
    KEY.write_text(json.dumps({name: result.state for name, _, result in chosen}, indent=2) + "\n")
    print(f"{len(chosen)} cases ({len(failed)} the judge failed) written to {SHEET}")


def score() -> None:
    judge = json.loads(KEY.read_text())
    mine = {}
    for block in SHEET.read_text().split("\n## ")[1:]:
        label = re.search(r"^Label:[ \t]*(pass|fail)\b", block, re.M | re.I)
        if label:
            mine[block.split()[1]] = "passed" if label.group(1).lower() == "pass" else "failed"
    if not mine:
        sys.exit("no labels filled in yet")
    differ = [name for name, state in mine.items() if judge[name] != state]
    print(f"labelled {len(mine)} of {len(judge)}; the judge agreed on {len(mine) - len(differ)}")
    for name in differ:
        print(f"  {name}: you {mine[name]}, judge {judge[name]}")


if __name__ == "__main__":
    {"sheet": sheet, "score": score}[sys.argv[1] if len(sys.argv) > 1 else "sheet"]()
