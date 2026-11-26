"""The critic-optimizer loop: run, classify, patch one cluster, keep it only if it beats the noise."""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from . import checks, classify, counterfactual, fixer, judge, patch
from .llm import LLM
from .runtime import run_turn, save_agent
from .schemas import AgentDef, Case, Result

MAX_REFITS = 3
PLAIN = {
    "retrieval_miss": "the agent not finding the right passage",
    "hallucination": "the agent stating things the documents do not say",
    "wrong_refusal": "the agent refusing questions it could answer",
    "prompt_defect": "the agent mishandling text it had found",
}


def parallel(llm: LLM, fn, items: list) -> list:
    with ThreadPoolExecutor(llm.workers) as pool:
        return list(pool.map(fn, items))


def run_cases(llm: LLM, agent: AgentDef, index, cases: list[Case], judge_ok: bool,
              sample: int = 0) -> dict[str, Result]:
    index.chunks(agent.retrieval)  # build once, before the threads start

    def one(case):
        turn = run_turn(llm, agent, index, case.question, sample)
        return judge.evaluate(llm, case, turn, agent, index, sample, judge_ok)

    return {c.id: r for c, r in zip(cases, parallel(llm, one, cases))}


def memorizable(llm: LLM, agent: AgentDef, index, cases: list[Case]) -> list[str]:
    """Answerable cases whose key facts the agent produces with no documents at all."""

    def one(case):
        turn = run_turn(llm, agent, index, case.question, empty_context=True)
        if turn.status != "answered":
            return False
        ids = [f.id for f in case.key_facts]
        labels = judge.label(llm, case.question, turn.text, [], [(f.id, f.fact) for f in case.key_facts])
        hits = checks.facts_hit(case, turn.text)
        verdicts = judge.fact_verdicts(labels, ids) if labels else {}
        return all(i in hits or verdicts.get(i) == "present" for i in ids)

    answerable = [c for c in cases if c.expected_behavior == "answer" and c.key_facts]
    return [c.id for c, hit in zip(answerable, parallel(llm, one, answerable)) if hit]


def passed(results: dict[str, Result]) -> int:
    return sum(r.state == "passed" for r in results.values())


def refine(llm: LLM, agent: AgentDef, index, train: list[Case], required_refusals: list[str], judge_ok: bool,
           max_refits: int, run_dir, state: dict) -> AgentDef:
    """Fill `state` as it goes, so a spent budget still leaves something to report."""
    first = run_cases(llm, agent, index, train, judge_ok, sample=0)
    state.update(train_v0=first, train_final=first)
    second = run_cases(llm, agent, index, train, judge_ok, sample=1)
    flips = sum(first[c.id].state != second[c.id].state for c in train)
    noise = max(flips, 1)
    state.update(flips=flips, noise=noise)

    protected = [t for c in train for t in [c.question] + [x for f in c.key_facts for x in (f.fact, f.quote) if x]]
    current, results, history = agent, first, []
    for refit in range(1, min(max_refits, MAX_REFITS) + 1):
        def examine(case):
            result = results[case.id]
            category, note = classify.attribute(
                case, result, lambda: counterfactual.run(llm, current, index, case))
            if category not in classify.ALLOWED:
                return case, result, category, None, False
            return case, result, category, *classify.diagnose(llm, case, result, category, note, current)

        clusters: dict[tuple, list] = defaultdict(list)
        failed = [c for c in train if results[c.id].state == "failed"]
        for case, result, category, diagnosis, disagreed in parallel(llm, examine, failed):
            if category == "eval_defect":
                state["quarantined"].add(case.id)
            if diagnosis:
                state["classified"] += 1
                state["classifier_disagreements"] += disagreed
                clusters[(category, diagnosis.subtype)].append((case, result, diagnosis))
        if not clusters:
            break
        rejected = {h["cluster"] for h in history if not h["accepted"]}
        key = max(clusters, key=lambda k: ("/".join(k) not in rejected, len(clusters[k])))
        category, subtype = key
        members = clusters[key]
        cluster = {"category": category, "subtype": subtype, "cases": [
            {"id": c.id, "question": c.question, "expected": "; ".join(f.fact for f in c.key_facts)
             or c.expected_behavior, "got": r.turn.text, "hypothesis": d.hypothesis} for c, r, d in members]}
        allowed = classify.ALLOWED[category]
        shown = [{k: h[k] for k in ("refit", "ops", "accepted", "fixed", "broke")} for h in history]
        proposal = fixer.propose(llm, current, cluster, allowed, shown)

        entry = {"refit": refit, "cluster": {"category": category, "subtype": subtype,
                                             "cases": [c.id for c, _, _ in members]},
                 "patch": patch.signature(proposal), "rationale": proposal.rationale,
                 "train_before": f"{passed(results)}/{len(train)}", "train_after": None,
                 "fixed": [], "broke": [], "noise_floor": noise, "accepted": False}
        try:
            candidate, changes = patch.apply(current, proposal, allowed, protected, history, required_refusals)
        except patch.PatchRejected as e:
            entry["rejected_by_code"] = str(e)
            entry["summary"] = f"Refit {refit}'s patch broke a rule ({e}), so it was never run."
        else:
            after = run_cases(llm, candidate, index, train, judge_ok)
            before_n, after_n = passed(results), passed(after)
            entry.update(
                patch=changes, train_after=f"{after_n}/{len(train)}", accepted=after_n - before_n > noise,
                fixed=[i for i in after if after[i].state == "passed" and results[i].state != "passed"],
                broke=[i for i in after if after[i].state != "passed" and results[i].state == "passed"])
            verdict = ("a bigger gain than the noise, so I kept it." if entry["accepted"]
                       else "not a bigger gain than the noise, so I put it back.")
            entry["summary"] = (f"Refit {refit} tried to stop {PLAIN[category]}. Train passes went from "
                                f"{before_n} to {after_n}: {verdict}")
            if entry["accepted"]:
                current, results = candidate, after
                state["train_final"] = results
                save_agent(current, run_dir / f"agent.v{current.version}.yaml")
                save_agent(current, run_dir / "agent.final.yaml")
            else:
                save_agent(candidate, run_dir / f"agent.refit{refit}.rejected.yaml")
        history.append({"refit": refit, "ops": patch.signature(proposal), "accepted": entry["accepted"],
                        "fixed": entry["fixed"], "broke": entry["broke"], "cluster": f"{category}/{subtype}"})
        state["log"].append(entry)
        print(f"      refit {refit}: {entry['summary']}", flush=True)
    return current
