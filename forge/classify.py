"""Attribution is a decision tree in code. The LLM only names the subtype, the fix target and a hypothesis."""

from .llm import LLM
from .schemas import SECTIONS, AgentDef, Case, Diagnosis, Result

SUBTYPES = {
    "retrieval_miss": ["lexical_mismatch", "top_k_too_low", "chunk_too_small", "chunk_too_large"],
    "prompt_defect": ["missed_key_fact", "format", "dropped_condition", "no_clarification", "tool_misuse",
                      "conflict_unhandled"],
    "hallucination": ["filled_gap", "wrong_number", "memory_answer"],
    "wrong_refusal": ["policy_too_broad", "threshold_too_strict"],
}
ALLOWED = {  # the first path is the default fix target
    "retrieval_miss": ["/retrieval/top_k", "/retrieval/bm25_weight", "/retrieval/chunk_size",
                       "/retrieval/chunk_overlap"],
    "prompt_defect": ["/system_prompt/grounding_rules"]
    + [f"/system_prompt/{s}" for s in SECTIONS if s != "grounding_rules"],
    "hallucination": ["/system_prompt/grounding_rules", "/system_prompt/refusal_policy", "/retrieval/min_score"],
    "wrong_refusal": ["/system_prompt/refusal_policy", "/retrieval/min_score", "/retrieval/top_k"],
}


def attribute(case: Case, result: Result, counterfactual) -> tuple[str, str]:
    """Return (category, note). `counterfactual()` is called only for retrieval failures."""
    if result.state == "unknown":
        return "judge_uncertain", "; ".join(result.reasons)
    if not result.contract_valid:
        return "prompt_defect", "the output contract was broken"
    if case.expected_behavior == "refuse" and result.turn.status == "answered":
        return "hallucination", "answered a question that should be refused"
    if result.gold_in_topk is False:
        passes, supports, why = counterfactual()
        if passes:
            return "retrieval_miss", "passes once the gold chunk is injected"
        if not supports:
            return "eval_defect", "the gold chunk does not support the gold fact"
        return "retrieval_miss", f"still fails with the gold chunk injected: {why}"
    if case.expected_behavior == "answer" and result.turn.status == "refused" and result.gold_in_topk:
        return "wrong_refusal", "refused although the needed text was retrieved"
    if result.unsupported or result.contradicted:
        return "hallucination", "stated something the context does not support"
    return "prompt_defect", "had the context and still got it wrong"


def diagnose(llm: LLM, case: Case, result: Result, category: str, note: str,
             agent: AgentDef) -> tuple[Diagnosis, bool]:
    """Return (diagnosis, whether the model disagreed with the tree)."""
    out = llm.ask("06_classifier", {
        "case_json": {"id": case.id, "question": case.question, "expected_behavior": case.expected_behavior,
                      "key_facts": [f.fact for f in case.key_facts]},
        "got_json": {"status": result.turn.status, "answer": result.turn.text},
        "signals_json": {
            "contract_valid": result.contract_valid, "gold_in_topk": result.gold_in_topk,
            "gold_rank": result.gold_rank, "counterfactual_pass": note.startswith("passes") or None,
            "unsupported_claims": result.unsupported, "contradicted_claims": result.contradicted,
            "missing_key_facts": result.missing_facts, "tools_expected": case.expected_tools,
            "tools_called": [c.name for c in result.turn.tool_calls]},
        "locked_category": f'"{category}"',
        "agent_json": {"prompt_sections": list(agent.system_prompt), "retrieval": agent.retrieval.model_dump()},
    }, Diagnosis, "classifier")
    disagreed = bool(out and out.category != category)
    out = out or Diagnosis(category=category, subtype="", hypothesis=note)
    out.category = category
    if out.subtype not in SUBTYPES[category]:
        out.subtype = "format" if not result.contract_valid else SUBTYPES[category][0]
    if out.fix_target not in ALLOWED[category]:
        out.fix_target = ALLOWED[category][0]
    return out, disagreed
