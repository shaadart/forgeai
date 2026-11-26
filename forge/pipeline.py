"""The eight stages in order. Each writes its output to the run folder before the next starts."""

import json
from pathlib import Path

from pydantic import BaseModel

from . import (canaries, classify, counterfactual, evalgen, generator, groundability, intake, inventory, loop,
               report, split)
from .index import Index
from .llm import LLM, BudgetExceeded
from .runtime import save_agent

OK, NOT_GROUNDABLE, BUDGET_SPENT, CRASHED = 0, 2, 3, 4


def _plain(value):
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(type(value).__name__)


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=_plain) + "\n")


def save_lines(path: Path, rows: list) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, default=_plain) + "\n" for r in rows))


def stage(number: int, yard: str, name: str, note: str = "") -> None:
    print(f"[{number}/8 {yard:<14}] {name:<13} {note}", flush=True)


def build(run_dir: Path, brief: str, docs_dir: Path, llm: LLM, embed, unattended: bool = True,
          answers: dict | None = None, max_refits: int = loop.MAX_REFITS) -> int:
    run_dir.mkdir(parents=True, exist_ok=True)
    state = {"log": [], "categories": {}, "quarantined": set(), "cases": {}, "classified": 0,
             "classifier_disagreements": 0, "name": "(unnamed agent)"}
    try:
        code = _stages(run_dir, brief, docs_dir, llm, embed, unattended, answers, max_refits, state)
        if code == NOT_GROUNDABLE:
            return code
    except BudgetExceeded as e:
        state["stopped"] = str(e)
        code = BUDGET_SPENT
    _report(run_dir, llm, state)
    return code


def _stages(run_dir, brief, docs_dir, llm, embed, unattended, answers, max_refits, state) -> int:
    docs = inventory.scan(docs_dir)
    save(run_dir / "inventory.json", [d.model_dump(exclude={"segments", "records"}) for d in docs])
    state["not_read"] = [f"{d.name} ({d.note})" for d in docs if not d.read or d.note]
    if not any(d.read for d in docs):  # say so before a single model call is paid for
        listing = "".join(f"- {d.name}: {d.note}\n" for d in docs) or "- the folder is empty\n"
        (run_dir / "report.md").write_text(f"# Not built: no readable documents in {docs_dir}\n\n{listing}")
        print(f"stopped: no readable documents in {docs_dir}")
        return NOT_GROUNDABLE

    saved = run_dir / "interview.json"
    if saved.is_file():  # resume: never ask a person twice
        record = json.loads(saved.read_text())
        stage(1, "OWNER'S SPEC", "intake", "answers reused")
    else:
        asked, dropped = intake.questions(llm, brief, docs, embed)
        save(run_dir / "questions.json", {"asked": asked, "dropped": dropped})
        record = intake.interview(asked, unattended, answers)
        save(saved, record)
        assumed = sum(r["source"] == "default" for r in record)
        stage(1, "OWNER'S SPEC", "intake", f"{len(record)} questions, {assumed} answered by default (ASSUMED)")
    requirements = intake.requirements(llm, brief, docs, record)
    save(run_dir / "requirements.json", requirements)

    index = Index(docs, embed, docs_dir)
    final, table, stop = groundability.apply(llm, index, requirements)
    save(run_dir / "groundability.json", table)
    save(run_dir / "requirements.final.json", final)
    verdicts = [r["verdict"] for r in table]
    stage(2, "LOAD LINE", "groundability", ", ".join(f"{verdicts.count(v)} {v}" for v in groundability.ORDER))
    state.update(assumptions=[a.text for a in final.assumptions],
                 demoted=[r["topic"] for r in table if r["verdict"] == "unsupported"])
    if stop:
        (run_dir / "report.md").write_text(report.not_groundable(final, table))
        print(f"stopped: the brief is not groundable. See {run_dir / 'report.md'}")
        return NOT_GROUNDABLE

    agent, defects = generator.generate(llm, final, docs, docs_dir, run_dir)
    save_agent(agent, run_dir / "agent.v0.yaml")
    save_agent(agent, run_dir / "agent.final.yaml")
    save(run_dir / "generator_log.json", defects)
    state.update(name=agent.name, generator_defects=defects, tools=[t.name for t in agent.tools])
    stage(3, "DRAWING OFFICE", "generator", f"agent.v0.yaml  tools: {', '.join(state['tools']) or 'none'}")

    cases, rejected, stats = evalgen.build(llm, index, final, agent)
    cases, linking = split.unlink(cases)
    rejected += [{"gate": "split", "reason": "links so many chunks that nothing could be sealed",
                  "category": c.category, "case": c} for c in linking]
    stats.update(kept=len(cases), rejected=len(rejected), below_minimum=len(cases) < evalgen.MINIMUM,
                 lexical_overlap=sum("lexical_overlap" in c.flags for c in cases))
    save_lines(run_dir / "evalset.rejected.jsonl", rejected)
    train, sealed, record = split.split(cases)
    save(run_dir / "split.json", record)
    save_lines(run_dir / "evalset.jsonl", train + sealed)
    state.update(evalset=stats, cases={c.id: c for c in train + sealed})
    stage(4, "SEA TRIALS", "evalgen",
          f"{stats['generated']} generated, {stats['rejected']} rejected, {len(train)} train / {len(sealed)} sealed")
    if not train:
        state["stopped"] = "no eval case survived the gates, so nothing could be tested"
        return OK

    checks = canaries.run(llm, train + sealed, index.chunks(agent.retrieval))
    save(run_dir / "canaries.json", checks)
    judge_ok = canaries.healthy(checks)
    state["canaries"] = checks
    stage(5, "SURVEY", "judge", f"canaries {sum(c['ok'] for c in checks)}/{len(checks)}")
    state["sealed_v0"] = loop.run_cases(llm, agent, index, sealed, judge_ok)
    state["memorizable"] = loop.memorizable(llm, agent, index, train + sealed)

    stage(6, "REFIT", "loop", f"at most {min(max_refits, loop.MAX_REFITS)}")
    best = loop.refine(llm, agent, index, train, [t.topic for t in final.must_refuse], judge_ok,
                       max_refits, run_dir, state)
    state["sealed_final"] = loop.run_cases(llm, best, index, sealed, judge_ok)

    # final attribution, by the code tree only: sealed cases are never shown to the classifier or the fixer
    def attribute(item):
        case_id, result = item
        case = state["cases"][case_id]
        return case_id, classify.attribute(case, result, lambda: counterfactual.run(llm, best, index, case))

    failing = [item for results in (state["train_final"], state["sealed_final"])
               for item in results.items() if item[1].state != "passed"]
    for case_id, category in loop.parallel(llm, attribute, failing):
        state["categories"][case_id] = category
        if category[0] == "eval_defect":
            state["quarantined"].add(case_id)
    return OK


def _report(run_dir: Path, llm: LLM, state: dict) -> None:
    save_lines(run_dir / "iterations.jsonl", state["log"])
    for key in ("train_v0", "train_final", "sealed_v0", "sealed_final"):
        if state.get(key) is not None:
            save(run_dir / f"results.{key}.json", state[key])
    card = report.scorecard(state, llm.usage(), dict(llm.contract_failures))
    known = report.facts(card)
    warning = "judge.canaries" if card["judge"]["health"] == "degraded" else None
    prose = None
    if not card["stopped"]:
        prose = report.write_prose(llm, known, card["failures"], warning)
    card["budget"], card["contract_failures"] = llm.usage(), dict(llm.contract_failures)
    save(run_dir / "scorecard.json", card)
    (run_dir / "report.md").write_text(report.render(card, state, prose))
    stage(7, "CERTIFICATE", "report",
          f"sealed {report.headline(card['sealed']['final'])}, {len(card['failures'])} conditions of class")
    if (run_dir / "agent.final.yaml").is_file():
        stage(8, "BRIDGE", "ready", f"forge chat {run_dir / 'agent.final.yaml'}")
