"""The certificate. Code renders every number; the model writes prose and may not type a digit."""

import math
import re

from pydantic import model_validator

from .llm import LLM, BudgetExceeded, LLMError, fill, load_prompt
from .schemas import Case, Prose, Result

BANNED = ("robust", "seamless", "perfect", "guarantee", "flawless", "excellent", "state-of-the-art")
NUMBER_WORDS = (  # "one" is left out: it is an ordinary pronoun
    "zero two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
    "eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million half halves "
    "third thirds quarter quarters dozen twice").split()
REF = re.compile(r"\[\[([\w.]+)\]\]")
CASE_ID = re.compile(r"\b[TS]\d{2,}\b")
MEMO_WARNING = 0.30
GAP_WARNING = 0.15


def wilson(passed: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if not total:
        return 0.0, 1.0
    p = passed / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return max(centre - half, 0.0), min(centre + half, 1.0)


def tally(results: dict[str, Result] | None, skip: set = frozenset(), only: set | None = None) -> dict | None:
    """Unknown is not zero: it counts neither as a pass nor as a fail."""
    if results is None:
        return None
    states = ["unknown" if i in skip else r.state for i, r in results.items() if only is None or i in only]
    passed, failed = states.count("passed"), states.count("failed")
    decided = passed + failed
    low, high = wilson(passed, decided)
    return {"passed": passed, "failed": failed, "unknown": states.count("unknown"), "total": len(states),
            "rate": passed / decided if decided else None, "ci": [low, high]}


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{round(value * 100)}%"


def headline(t: dict | None) -> str:
    if t is None:
        return "not run"
    return f"{t['passed']} passed, {t['failed']} failed, {t['unknown']} unknown ({pct(t['rate'])})"


def _interval(t: dict | None) -> str:
    if t is None or t["rate"] is None:
        return "n/a"
    return f"{pct(t['ci'][0])} to {pct(t['ci'][1])}"


def _why_open(case: Case, category: str, log: list[dict]) -> str:
    if category == "judge_uncertain":
        return "The judge could not decide, so it was never sent to the fixer."
    if category == "eval_defect":
        return "The test itself looks wrong, so it is quarantined."
    if case.id.startswith("S"):
        return "Sealed case: never shown to the fixer."
    for entry in reversed(log):
        if case.id in entry["broke"] and entry["accepted"]:
            return f"Refit {entry['refit']} was kept and broke this case."
        if case.id in entry["cluster"]["cases"]:
            if "rejected_by_code" in entry:
                return f"Refit {entry['refit']} targeted it; code rejected the patch: {entry['rejected_by_code']}."
            outcome = "was kept but did not fix it" if entry["accepted"] else "did not beat the noise floor"
            return f"Refit {entry['refit']} targeted it and {outcome}."
    return "No refit targeted this failure before the refits ran out."


def conditions(state: dict) -> list[dict]:
    rows = []
    for split_name, results in (("train", state.get("train_final")), ("sealed", state.get("sealed_final"))):
        for case_id, result in (results or {}).items():
            category, note = state["categories"].get(case_id, (None, ""))
            if result.state == "passed" and case_id not in state["quarantined"]:
                continue
            category = category or ("judge_uncertain" if result.state == "unknown" else "unclassified")
            case = state["cases"][case_id]
            evidence = "; ".join(result.reasons) or note or "no evidence recorded"
            rows.append({"id": case_id, "split": split_name, "category": category,
                         "question": case.question, "got": result.turn.text[:300], "evidence": evidence[:300],
                         "note": note, "still_open_because": _why_open(case, category, state["log"])})
    return rows


def scorecard(state: dict, usage: dict, contract_failures: dict) -> dict:
    skip = state["quarantined"]
    memo = set(state.get("memorizable") or [])
    cases = state.get("cases", {})
    probed = [c for c in cases.values() if c.expected_behavior == "answer"]
    train = tally(state.get("train_final"), skip)
    sealed = tally(state.get("sealed_final"), skip)
    gap = (train["rate"] - sealed["rate"]
           if train and sealed and train["rate"] is not None and sealed["rate"] is not None else None)
    finals = {**(state.get("train_final") or {}), **(state.get("sealed_final") or {})}
    canary = state.get("canaries")
    called = {c.name for r in finals.values() for c in r.turn.tool_calls}
    return {
        "name": state.get("name"),
        "train": {"v0": tally(state.get("train_v0"), skip), "final": train},
        "sealed": {"v0": tally(state.get("sealed_v0"), skip), "final": sealed,
                   "final_without_memorizable": tally(
                       state.get("sealed_final"), skip, set(finals) - memo) if state.get("sealed_final") else None},
        "train_sealed_gap": gap,
        "likely_overfitting": gap is not None and gap > GAP_WARNING,
        "noise": {"flips": state.get("flips"), "floor": state.get("noise")},
        "loop": {"accepted": sum(e["accepted"] for e in state["log"]),
                 "rejected": sum(not e["accepted"] for e in state["log"])},
        "judge": {"health": None if canary is None else
                  ("ok" if all(c["ok"] for c in canary) and canary else "degraded"),
                  "canaries": canary,
                  "shuffle_disagreements": sum(r.shuffle_disagree for r in finals.values()),
                  "number_disagreements": sum(r.number_disagree for r in finals.values()),
                  "judged": len(finals)},
        "classifier": {"disagreements": state["classifier_disagreements"], "classified": state["classified"]},
        "evalset": state.get("evalset"),
        "memorizable": {"cases": sorted(memo), "rate": len(memo) / len(probed) if probed else None},
        "assumptions": state.get("assumptions", []),
        "demoted_topics": state.get("demoted", []),
        "generator_defects": state.get("generator_defects", []),
        "unused_tools": sorted(set(state.get("tools", [])) - called) if finals else [],
        "documents_not_read": state.get("not_read", []),
        "answer_words": {k: round(sum(r.answer_words for r in state[k].values()) / len(state[k]), 1)
                         for k in ("train_v0", "train_final") if state.get(k)},
        "contract_failures": contract_failures,
        "budget": usage,
        "stopped": state.get("stopped"),
        "failures": conditions(state),
    }


def warnings(card: dict) -> list[str]:
    found = []
    if card["judge"]["health"] == "degraded":
        failed = ", ".join(c["name"] for c in card["judge"]["canaries"] if not c["ok"]) or "none ran"
        found.append(f"THE SCORES BELOW ARE UNRELIABLE: the judge failed its planted checks ({failed}).")
    if card["stopped"]:
        found.append(f"This run stopped early: {card['stopped']}")
    if (card["memorizable"]["rate"] or 0) > MEMO_WARNING:
        found.append(f"{pct(card['memorizable']['rate'])} of answerable cases can be answered without the "
                     "documents, so the score partly measures what the model already knew.")
    if card["likely_overfitting"]:
        cause = ("the refits likely overfitted." if card["loop"]["accepted"]
                 else "no refit was kept, so this is chance or an uneven split, not overfitting.")
        found.append(f"Train is more than 15 points above sealed: {cause}")
    if card["evalset"] and card["evalset"]["below_minimum"]:
        found.append(f"Only {card['evalset']['kept']} eval cases survived the gates; 20 are required.")
    return found


def facts(card: dict) -> dict[str, str]:
    out = {}
    for name, key in (("train", "train"), ("sealed", "held_out")):
        for version in ("v0", "final"):
            t = card[name][version]
            out[f"{key}.{version}"] = headline(t)
        final = card[name]["final"] or {}
        out[f"{key}.pass_rate"] = pct(final.get("rate"))
        out[f"{key}.passed"] = str(final.get("passed", "n/a"))
        out[f"{key}.total"] = str(final.get("total", "n/a"))
        out[f"{key}.ci"] = _interval(card[name]["final"])
    judge, evalset = card["judge"], card["evalset"] or {}
    canary = judge["canaries"] or []
    out |= {
        "judge.canaries": f"{sum(c['ok'] for c in canary)} of {len(canary)}",
        "judge.shuffle_disagree": f"{judge['shuffle_disagreements']} of {judge['judged']}",
        "judge.number_disagree": f"{judge['number_disagreements']} of {judge['judged']}",
        "evalset.generated": str(evalset.get("generated", 0)),
        "evalset.rejected": str(evalset.get("rejected", 0)),
        "evalset.lexical_overlap": str(evalset.get("lexical_overlap", 0)),
        "memo.rate": pct(card["memorizable"]["rate"]),
        "noise.flips": str(card["noise"]["flips"]),
        "loop.accepted": str(card["loop"]["accepted"]),
        "loop.rejected": str(card["loop"]["rejected"]),
        "budget.used": str(card["budget"]["tokens"]),
        "assumptions.list": " ".join(card["assumptions"]) or "none",
        "groundability.demoted": ", ".join(card["demoted_topics"]) or "none",
    }
    for row in card["failures"]:
        out[f"failures.{row['id']}.evidence"] = row["evidence"]
        out[f"failures.{row['id']}.still_open_because"] = row["still_open_because"]
    return out


def check_prose(prose: Prose, known: dict, failure_ids: set[str]) -> str | None:
    text = "\n".join(prose.model_dump().values())
    unknown = [k for k in REF.findall(text) if k not in known]
    if unknown:
        return f"unknown key [[{unknown[0]}]]"
    bare = CASE_ID.sub("", REF.sub("", text)).replace("95%", "")  # the prompt's own example says "95% interval"
    if re.search(r"\d", bare):
        return "you typed a digit; use a [[key]] instead"
    words = set(re.findall(r"[a-z\-]+", bare.lower()))
    if number := words & set(NUMBER_WORDS):
        return f"you typed the number word {sorted(number)[0]!r}; use a [[key]] instead"
    if banned := [w for w in BANNED if w in bare.lower()]:
        return f"banned word: {banned[0]}"
    missing = failure_ids - set(CASE_ID.findall(prose.what_still_fails))
    if missing:
        return f"what_still_fails leaves out: {', '.join(sorted(missing))}"
    return None


def write_prose(llm: LLM, known: dict, rows: list[dict], warning_key: str | None) -> Prose | None:
    ids = {r["id"] for r in rows}

    class Checked(Prose):
        @model_validator(mode="after")
        def _rules(self):
            if error := check_prose(self, known, ids):
                raise ValueError(error)
            return self

    meta, blocks = load_prompt("08_report")
    failures = [{"id": r["id"], "split": r["split"], "category": r["category"],
                 "evidence_key": f"failures.{r['id']}.evidence",
                 "open_key": f"failures.{r['id']}.still_open_because"} for r in rows]
    message = fill(blocks[""], {"facts_json": known, "failures_json": failures,
                                "headline_warning_key": warning_key or "null"})
    try:
        prose = llm.parsed(meta["side"], [{"role": "user", "content": message}], float(meta["temperature"]),
                           Checked, "report")
    except (BudgetExceeded, LLMError):
        return None
    if prose is None:
        return None
    return Prose(**{k: REF.sub(lambda m: known[m.group(1)], v) for k, v in prose.model_dump().items()})


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def render(card: dict, state: dict, prose: Prose | None) -> str:
    lines = [f"# Certificate: {card['name']}, issued with {len(card['failures'])} conditions of class", ""]
    lines += [f"> **{w}**\n>" for w in warnings(card)]
    if prose is None:
        lines.append("> The prose writer failed or was skipped; this report is the plain code-rendered template.")
    lines += ["", "| | Baseline (v0) | Final |", "|---|---|---|"]
    for name in ("train", "sealed"):
        final = headline(card[name]["final"])
        if name == "sealed" and card[name]["final"]:
            final += f", 95% interval {_interval(card[name]['final'])}"
        lines.append(f"| {name.title()} | {headline(card[name]['v0'])} | {final} |")
    budget = card["budget"]
    lines += [
        "", f"Noise floor: {card['noise']['flips']} cases flip between identical runs; a refit is kept only if its "
        f"gain is larger than {card['noise']['floor']}.",
        f"Refits: {card['loop']['accepted']} accepted, {card['loop']['rejected']} rejected.",
        f"A full run is {budget['calls']} model calls and {budget['tokens']} tokens "
        f"(budget {budget['limit']}), {budget['seconds']} seconds of model time.", ""]
    if prose:
        lines += ["## Summary", "", prose.summary, ""]
    lines += ["## Conditions of class: what still fails", ""]
    if card["failures"]:
        lines += ["| Case | Split | Category | Question | Evidence | Why still open |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['id']} | {r['split']} | {r['category']} | {_cell(r['question'])} | {_cell(r['evidence'])} "
                  f"| {_cell(r['still_open_because'])} |" for r in card["failures"]]
    else:
        lines.append("No case is open. Treat this with suspicion: check the size and difficulty of the eval set.")
    if state["log"]:
        lines += ["", "## Refit log", ""] + [f"- {e['summary']}" for e in state["log"]]
    if prose:
        lines += ["", "## What still fails", "", prose.what_still_fails, "", "## Why, by category", "",
                  prose.why_by_category]
    known = facts(card)
    lines += [
        "", "## What I doubt about this run", "",
        f"- Judge: canaries passed {known['judge.canaries']}; shuffle disagreement "
        f"{known['judge.shuffle_disagree']}; number-check disagreement {known['judge.number_disagree']}.",
        f"- Classifier disagreed with the code tree on {card['classifier']['disagreements']} of "
        f"{card['classifier']['classified']} diagnoses.",
        f"- Eval set: {known['evalset.rejected']} of {known['evalset.generated']} generated cases rejected; "
        f"{known['evalset.lexical_overlap']} kept questions copy 5+ words from their source.",
        f"- Memorizable cases: {known['memo.rate']}. Sealed without them: "
        f"{headline(card['sealed']['final_without_memorizable'])}.",
        f"- Assumptions made without the requester: {known['assumptions.list']}",
        f"- Topics refused because the documents cannot support them: {known['groundability.demoted']}.",
        f"- Documents not read: {', '.join(card['documents_not_read']) or 'none'}.",
        f"- Tools attached but never called: {', '.join(card['unused_tools']) or 'none'}.",
        f"- Generator defects fixed by code: {'; '.join(card['generator_defects']) or 'none'}.",
        f"- Model replies that broke their contract twice, by stage: {card['contract_failures'] or 'none'}.",
        "- The eval set was written by a small model, so it covers the questions a small model thinks to ask.",
        "- The counterfactual puts the gold chunk first, the best case, so it can overstate how fixable a miss is.",
    ]
    if card["evalset"] and card["evalset"]["groundability_disagreements"]:
        lines.append("- Questions meant to be refused that the documents answer: "
                     + "; ".join(card["evalset"]["groundability_disagreements"]))
    if prose:
        lines += ["", prose.pipeline_doubts, "", "## What I would fix next", "", prose.next_fixes]
    return "\n".join(lines) + "\n"


def not_groundable(requirements, table: list[dict]) -> str:
    lines = ["# Not built: the brief is not groundable", "",
             "More than half of the must-answer topics are not supported by the documents, so no agent was "
             "generated. An agent built anyway would have to guess.", "",
             "| Topic | Verdict | What is missing |", "|---|---|---|"]
    lines += [f"| {_cell(r['topic'])} | {r['verdict']} | {_cell(r['missing'])} |" for r in table]
    if not table:
        lines.append("| (no topic found in the brief) | unsupported | |")
    lines += ["", "## Assumptions", ""] + [f"- {a.text}" for a in requirements.assumptions]
    return "\n".join(lines) + "\n"
