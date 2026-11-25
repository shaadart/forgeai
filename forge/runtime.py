"""run_turn(): the one code path shared by the eval harness and the chat runner."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from . import tools
from .llm import LLM, fill, load_prompt, parse_json
from .schemas import SECTIONS, AgentDef, Chunk, Reply, ToolCall, Turn

MAX_TOOL_CALLS = 4


def system_prompt(agent: AgentDef) -> str:
    instructions = "\n\n".join(f"## {s}\n{agent.system_prompt[s]}" for s in SECTIONS if s in agent.system_prompt)
    blocks = load_prompt("09_agent_runtime")[1]
    tool_block = ""
    if agent.tools:
        listing = "\n".join(f"- {t.name}: {tools.REGISTRY[t.name]['description']} args: "
                            f"{tools.REGISTRY[t.name]['args']}" for t in agent.tools)
        files = [name for name in agent.documents if name.lower().endswith(".csv")]
        if files:
            listing += f"\nCSV files: {', '.join(files)}"
        tool_block = "\n" + fill(blocks["tools"], {"tool_list": listing})
    return fill(blocks[""], {"instructions": instructions, "refusal_message": agent.refusal_message,
                             "tool_block": tool_block})


def run_turn(llm: LLM, agent: AgentDef, index, question: str, sample: int = 0,
             inject: list[Chunk] = (), empty_context: bool = False) -> Turn:
    if empty_context:  # no documents at all, so no tool that reads them either
        agent = agent.model_copy(update={"tools": []})
    retrieved = [] if empty_context else index.search(question, agent.retrieval)
    if inject:  # counterfactual: gold at rank 1, lowest-ranked chunks dropped
        known = {c.text for c in inject}
        rest = [c for c in retrieved if c.text not in known]
        retrieved = list(inject) + rest[: max(agent.retrieval.top_k - len(inject), 0)]
    if not retrieved and not agent.tools and not empty_context:  # the min_score gate
        return Turn(status="refused", answer=agent.refusal_message)

    # short labels in the prompt: a small model reads "## 6." in a chunk and invents an id such as "s6#c1"
    labels = {f"C{n}": c.chunk_id for n, c in enumerate(retrieved, 1)}
    context = "\n\n".join(f"[C{n}] (file: {c.doc})\n{c.text}" for n, c in enumerate(retrieved, 1)) or "(nothing found)"
    messages = [{"role": "system", "content": system_prompt(agent)},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"}]
    attached = {t.name for t in agent.tools}
    calls: list[ToolCall] = []
    repaired = False
    while True:
        text = llm.chat("builder", messages, 0.0, "agent", sample)
        try:
            obj = parse_json(text)
            if "tool_call" in obj:
                if len(calls) >= MAX_TOOL_CALLS:
                    raise ValueError("no more tool calls are allowed; send the final reply")
                request = obj["tool_call"] if isinstance(obj["tool_call"], dict) else {}
                name = str(request.get("name"))
                args = request.get("args") if isinstance(request.get("args"), dict) else {}
                if name in attached:
                    call = tools.call(name, args, index.docs)
                else:
                    call = ToolCall(name=name, args=args, result="error: you do not have this tool", ok=False)
                calls.append(call)
                messages = messages + [{"role": "assistant", "content": text},
                                       {"role": "user", "content": f"TOOL RESULT ({name}):\n{call.result}"}]
                continue
            reply = Reply.model_validate(obj)
            for citation in reply.citations:  # an unknown label stays as written and fails check 3
                citation.chunk_id = labels.get(citation.chunk_id, citation.chunk_id)
            return Turn(**reply.model_dump(), retrieved=retrieved, tool_calls=calls)
        except (ValueError, ValidationError) as e:
            if repaired:
                with llm.lock:
                    llm.contract_failures["agent"] += 1
                return Turn(status="refused", answer=agent.refusal_message, retrieved=retrieved,
                            tool_calls=calls, contract_valid=False)
            repaired = True
            repair = fill(load_prompt("00_repair")[1][""], {"validation_error": str(e)[:600]})
            messages = messages + [{"role": "assistant", "content": text}, {"role": "user", "content": repair}]


def save_agent(agent: AgentDef, path: Path) -> None:
    path.write_text(yaml.safe_dump(agent.model_dump(), sort_keys=False, allow_unicode=True, width=100))


def load_agent(path: Path) -> AgentDef:
    agent = AgentDef.model_validate(yaml.safe_load(Path(path).read_text()))
    unknown = [t.name for t in agent.tools if t.name not in tools.REGISTRY]
    if unknown:
        raise ValueError(f"unknown tool(s) in {path}: {', '.join(unknown)}")
    return agent


def stale_documents(agent: AgentDef, docs: list) -> list[str]:
    """Files added, removed or changed since the agent was evaluated."""
    current = {d.name: d.sha256 for d in docs}
    return sorted(n for n in current.keys() | agent.documents.keys() if current.get(n) != agent.documents.get(n))
