"""Ask the builder model for a small patch for one failure cluster."""

from .llm import LLM
from .patch import MAX_ADDED_WORDS, MAX_OPS
from .schemas import BOUNDS, AgentDef, Patch, PatchOp


def propose(llm: LLM, agent: AgentDef, cluster: dict, allowed: list[str], history: list[dict]) -> Patch:
    patch = llm.ask("07_fixer", {
        "max_ops": MAX_OPS, "max_added_words": MAX_ADDED_WORDS,
        "agent_json": {"system_prompt": agent.system_prompt, "retrieval": agent.retrieval.model_dump()},
        "cluster_json": cluster, "allowed_paths_json": allowed, "bounds_json": BOUNDS, "history_json": history,
    }, Patch, "fixer")
    if patch:
        return patch
    if cluster["category"] == "retrieval_miss":  # deterministic fallback: look a little wider
        top_k = min(agent.retrieval.top_k + 2, BOUNDS["top_k"][1])
        return Patch(rationale="fixer reply unusable; widen retrieval",
                     ops=[PatchOp(op="set", path="/retrieval/top_k", value=top_k)])
    return Patch(rationale="fixer reply unusable", ops=[])
