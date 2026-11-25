"""Blind LLM labels, twice with different evidence order. Code turns labels into passed / failed / unknown."""

import random
import re

from . import checks
from .llm import LLM
from .schemas import AgentDef, Case, Labels, Result, Turn

# "The assistant cannot help with wages" reports the reply itself. The prompt says to skip it; small judges do not.
ABOUT_THE_REPLY = re.compile(r"(?i)\s*(i|(the )?(assistant|answer|reply|response))\b.*?"
                             r"\b(declines?|refuses?|cannot|can't|could ?n[o']t|unable)\b")
REFERRAL = re.compile(r"(?i)\brephras|\b(ask|contact|refer)\w*\b.*\b(manager|responsible|department)\b|"
                      r"\b(not (be )?|can't |cannot (be )?)f(i|ou)nd\b")


def _boilerplate(claim: str, refusing: bool) -> bool:
    """In a refusal, "ask your manager" and "not found" state no document fact. A number always gets checked."""
    return refusing and bool(REFERRAL.search(claim)) and not re.search(r"\d", claim)


def label(llm: LLM, question: str, answer: str, evidence: list[str], facts: list[tuple[str, str]],
          sample: int = 0) -> Labels | None:
    items = [{"id": f"E{i}", "text": text} for i, text in enumerate(evidence, 1)]
    labels = llm.ask("05_judge", {
        "question": question, "evidence_json": items, "answer": answer,
        "key_facts_json": [{"id": i, "fact": f} for i, f in facts],
    }, Labels, "judge", sample)
    if labels is None:
        return None
    labels.claims = [c for c in labels.claims  # a question states no fact
                     if not c.claim.rstrip().endswith("?") and not ABOUT_THE_REPLY.match(c.claim)
                     and not _boilerplate(c.claim, labels.is_refusal)]
    known = {item["id"] for item in items}
    for claim in labels.claims:
        cited = re.findall(r"E\d+", claim.evidence_id or "")
        if cited and set(cited) <= known:  # "E1, E5" cites two real items
            claim.evidence_id = cited[0]
        if claim.evidence_id not in known:
            if claim.evidence_id or claim.verdict != "unsupported":
                claim.verdict, claim.evidence_id = "unsupported", None
    return labels


def fact_verdicts(labels: Labels, ids: list[str]) -> dict[str, str]:
    given = {f.id: f.verdict for f in labels.key_facts}
    return {i: given.get(i, "absent") for i in ids}


def outcome(labels: Labels, ids: list[str]) -> tuple:
    """What can change a verdict. Claim wording and splitting differ between passes, so they are not compared."""
    verdicts = {c.verdict for c in labels.claims}
    return ("unsupported" in verdicts, "contradicted" in verdicts, tuple(fact_verdicts(labels, ids).values()),
            labels.is_refusal, labels.asks_clarification)


def disagree(behavior: str, first: Labels, second: Labels, ids: list[str]) -> bool:
    """Compare only what the pass rule reads for this behaviour: "try rephrasing" must not unsettle a refusal."""
    read = {"answer": (0, 1, 2), "refuse": (0, 1, 3), "clarify": (0, 1, 2, 4)}[behavior]
    a, b = outcome(first, ids), outcome(second, ids)
    return any(a[i] != b[i] for i in read)


def passes(behavior: str, labels: Labels, facts_present: bool) -> bool:
    if any(c.verdict != "supported" for c in labels.claims):
        return False
    if behavior == "refuse":
        return labels.is_refusal
    if behavior == "clarify":
        return labels.asks_clarification or facts_present
    return facts_present


def evaluate(llm: LLM, case: Case, turn: Turn, agent: AgentDef, index, sample: int = 0,
             judge_ok: bool = True) -> Result:
    hard = checks.hard_checks(case, turn, agent)
    evidence = list(dict.fromkeys([c.text for c in turn.retrieved]
                                  + [c.result for c in turn.tool_calls if c.ok]))
    random.Random(f"{case.id}:{sample}").shuffle(evidence)
    answer = checks.strip_citations(turn)
    facts = [(f.id, f.fact) for f in case.key_facts]
    ids = [i for i, _ in facts]
    first = label(llm, case.question, answer, evidence, facts, sample)
    second = label(llm, case.question, answer, evidence[::-1], facts, sample)

    result = Result(case_id=case.id, state="failed", turn=turn, reasons=list(hard),
                    contract_valid=turn.contract_valid, answer_words=len(answer.split()))
    hits = checks.facts_hit(case, answer)
    result.missing_facts = [f.fact for f in case.key_facts if f.id not in hits]
    if first:
        verdicts = fact_verdicts(first, ids)
        result.missing_facts = [f.fact for f in case.key_facts
                                if f.id not in hits and verdicts[f.id] != "present"]
        result.unsupported = [c.claim for c in first.claims if c.verdict == "unsupported"]
        result.contradicted = [c.claim for c in first.claims if c.verdict == "contradicted"]
    result.facts_present = not result.missing_facts
    result.shuffle_disagree = bool(first and second and disagree(case.expected_behavior, first, second, ids))
    bad = bool(result.unsupported or result.contradicted)
    result.number_flag = checks.number_flag(case, turn)
    result.number_disagree = bool(first and result.number_flag and not bad)

    if hard:  # code decided; the judge cannot overturn it
        pass
    elif not judge_ok:
        result.state, result.reasons = "unknown", ["a judge canary failed, so this label cannot be trusted"]
    elif first is None or second is None:
        result.state, result.reasons = "unknown", ["the judge returned no usable labels"]
    elif result.shuffle_disagree:
        result.state, result.reasons = "unknown", ["the two judge passes disagree"]
    elif result.number_disagree:
        result.state, result.reasons = "unknown", ["a number is not in the context, but the judge accepted it"]
    elif passes(case.expected_behavior, first, result.facts_present):
        result.state = "passed"
    else:
        result.reasons += [f"unsupported claim: {c}" for c in result.unsupported]
        result.reasons += [f"contradicted claim: {c}" for c in result.contradicted]
        if case.expected_behavior == "refuse" and not first.is_refusal:
            result.reasons.append("the judge does not read the reply as a refusal")
        elif case.expected_behavior != "refuse":
            result.reasons += [f"missing key fact: {f}" for f in result.missing_facts]

    if result.state != "passed":
        result.gold_in_topk = checks.gold_in(case, checks.context_chunks(turn))
        if result.gold_in_topk is not None:
            ranked = [c for c, _ in index.ranking(case.question, agent.retrieval)]
            result.gold_rank = checks.gold_rank(case, ranked)
    return result
