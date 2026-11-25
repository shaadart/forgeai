"""The inclining experiment: put the gold chunk in the context and see whether the answer changes."""

from . import checks, judge
from .llm import LLM
from .runtime import run_turn
from .schemas import AgentDef, Case


def run(llm: LLM, agent: AgentDef, index, case: Case) -> tuple[bool, bool, str]:
    """Return (passes with gold, gold supports its own facts, why it still fails)."""
    turn = run_turn(llm, agent, index, case.question, inject=case.source_chunks)
    result = judge.evaluate(llm, case, turn, agent, index)
    if result.state == "passed":
        return True, True, ""
    facts = checks.quoted(case)
    labels = judge.label(llm, case.question, " ".join(f.fact for f in facts),
                         [c.text for c in case.source_chunks], [(f.id, f.fact) for f in facts])
    supports = labels is None or all(c.verdict == "supported" for c in labels.claims)
    return False, supports, "; ".join(result.reasons)
