"""The drawing office: the model writes prompt sections, code decides numbers, contract and tools."""

import os
import re
from pathlib import Path

from . import tools
from .checks import numbers
from .llm import LLM
from .schemas import SECTIONS, AgentDef, GeneratedAgent, Requirements, Retrieval, ToolChoice

MAX_SECTION_WORDS = 120
LIST_MARK = re.compile(r"^\s*(\d+[.)]|[-*\u2022])\s*")
NO_TOOLS = "1. You have no tools. Quote numbers from the context; do not calculate."


def _fallback(req: Requirements) -> GeneratedAgent:
    topics = "; ".join(t.topic for t in req.must_answer)
    text = {
        "role": f"1. You help {req.audience} with questions about the documents.",
        "scope": f"1. You answer questions about: {topics}.\n2. Anything else is out of scope.",
        "audience_and_tone": f"1. Write for {req.audience}.\n2. Tone: {req.tone}.\n3. Put the direct answer first.",
        "grounding_rules": "1. Answer only from the context and tool results you are given.\n"
        "2. Never use outside knowledge.\n3. Keep every condition and exception the context states.",
        "refusal_policy": "1. If the context does not contain the answer, refuse, say what is missing, "
        "and do not estimate.",
        "clarification_policy": "1. If a question has two readings with different answers, ask which one is meant.",
        "citation_rules": "1. Cite the chunk for every fact, with a short exact quote.",
        "tool_rules": "1. Call a tool only when the context cannot answer without it.",
        "conflict_policy": "1. If two sources disagree, show both with citations and say they disagree.",
    }
    by_capability = {t["capability"]: name for name, t in tools.REGISTRY.items()}
    chosen = {}
    for topic in req.must_answer:
        for capability in topic.capabilities:
            if capability in by_capability:
                chosen.setdefault(by_capability[capability], []).append(topic.id)
    return GeneratedAgent(name="Document assistant", system_prompt=text,
                          tools=[ToolChoice(name=n, topic_ids=i, why="needed by a topic") for n, i in chosen.items()],
                          refusal_message="I can't find that in the documents. Try rephrasing, or ask your manager.")


def _trim(section: str) -> str:
    """Drop whole rules from the end until the section fits."""
    lines = section.strip().splitlines()
    while len(lines) > 1 and len(" ".join(lines).split()) > MAX_SECTION_WORDS:
        lines.pop()
    return " ".join("\n".join(lines).split(" ")[:MAX_SECTION_WORDS])


def drop_invented_numbers(section: str, allowed: set[float]) -> tuple[str, list[str]]:
    """Facts belong in the documents. A rule stating a number the requirements never mention was made up."""
    lines = section.strip().splitlines()
    invented = [ln for ln in lines if numbers(LIST_MARK.sub("", ln)) - allowed]
    return "\n".join(ln for ln in lines if ln not in invented), invented


def _add_rule(section: str, rule: str) -> str:
    return f"{section}\n{len(section.splitlines()) + 1}. {rule}".strip()


def generate(llm: LLM, req: Requirements, docs: list, docs_dir: Path, run_dir: Path) -> tuple[AgentDef, list[str]]:
    registry = [{k: t[k] for k in ("name", "capability", "description", "not_for")} for t in tools.REGISTRY.values()]
    draft = llm.ask("03_generator", {"requirements_json": req.model_dump(), "tools_json": registry},
                    GeneratedAgent, "generator")
    defects = []
    if draft is None:
        defects.append("generator reply unusable; used the template agent")
        draft = _fallback(req)

    has_csv = any(d.type == "csv" and d.read for d in docs)
    kept: dict[str, ToolChoice] = {}
    for choice in draft.tools:
        tool = tools.REGISTRY.get(choice.name)
        valid = [t.id for t in req.must_answer
                 if tool and t.id in choice.topic_ids and tool["capability"] in t.capabilities]
        if not valid or (choice.name == "csv_lookup" and not has_csv):
            defects.append(f"dropped tool {choice.name}: no supported topic needs it, or nothing for it to read")
        else:
            kept[choice.name] = ToolChoice(name=choice.name, topic_ids=valid, why=choice.why)

    prompt = {}
    allowed = numbers(req.model_dump_json())
    for name in SECTIONS:
        section, invented = drop_invented_numbers(draft.system_prompt[name], allowed)
        defects += [f"removed a rule with an invented number from {name}: {line.strip()[:120]}" for line in invented]
        section = section or _fallback(req).system_prompt[name]
        prompt[name] = _trim(section)
        if prompt[name] != section.strip():
            defects.append(f"trimmed section {name} to {MAX_SECTION_WORDS} words")
    if not kept:
        prompt["tool_rules"] = NO_TOOLS
    else:
        dropped = {t.name for t in draft.tools} - kept.keys()
        lines = [ln for ln in prompt["tool_rules"].splitlines()
                 if not any(re.search(rf"\b{re.escape(n)}\b", ln) for n in dropped)]
        prompt["tool_rules"] = "\n".join(lines) or "1. Call a tool only when the context cannot answer without it."
    for topic in req.must_refuse:
        if topic.topic.lower() not in prompt["refusal_policy"].lower():
            prompt["refusal_policy"] = _add_rule(
                prompt["refusal_policy"], f"Do not answer questions about {topic.topic}. Go to {topic.referral}.")
            defects.append(f"appended must-refuse topic missing from refusal_policy: {topic.topic}")
    for topic in req.must_answer:
        if topic.scope_note:
            prompt["scope"] = _add_rule(
                prompt["scope"], f"For {topic.topic}, the documents do not cover this: {topic.scope_note} "
                "Say so if asked.")

    agent = AgentDef(
        name=draft.name, docs_dir=os.path.relpath(Path(docs_dir).resolve(), Path(run_dir).resolve()),
        documents={d.name: d.sha256 for d in docs}, system_prompt=prompt, retrieval=Retrieval(),
        tools=list(kept.values()), refusal_message=draft.refusal_message)
    return agent, defects
