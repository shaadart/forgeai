"""The bridge: a generic chat runner for any agent definition."""

from pathlib import Path

from . import inventory
from .checks import context_chunks
from .index import Index
from .llm import LLM, BudgetExceeded, LLMError
from .runtime import load_agent, run_turn, stale_documents


def chat(path: Path, llm: LLM, embed, reindex: bool = False) -> int:
    agent = load_agent(path)
    folder = (Path(path).resolve().parent / agent.docs_dir).resolve()
    docs = inventory.scan(folder)
    stale = stale_documents(agent, docs)
    if stale and not reindex:
        print(f"documents changed since evaluation: {', '.join(stale)}\nRun again with --reindex to use them.")
        return 1
    if stale:
        print(f"warning: documents changed ({', '.join(stale)}); the evaluation results no longer apply.")
    index = Index(docs, embed, folder)
    print(f"{agent.name} (v{agent.version}). Each question stands alone. Empty line or Ctrl-D to leave.")
    while True:
        try:
            question = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not question:
            return 0
        try:
            turn = run_turn(llm, agent, index, question)
        except (LLMError, BudgetExceeded) as e:
            print(f"error: {e}")
            continue
        for call in turn.tool_calls:
            print(f"  [tool {call.name} {call.args}]")
        print(f"\n{turn.text}\n  ({turn.status})")
        texts = {c.chunk_id: c.text for c in context_chunks(turn)}
        for citation in turn.citations:
            print(f"\n  [{citation.chunk_id}] \"{citation.quote}\"")
            print(f"    {texts.get(citation.chunk_id, 'WARNING: this chunk was not in the context')[:600]}")
