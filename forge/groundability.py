"""The load line: the documents decide what the agent may answer, not the brief."""

import re

from .checks import quote_in
from .llm import LLM
from .loop import parallel
from .schemas import Chunk, Groundability, RefuseTopic, Requirements, Retrieval, Topic

WIDE = Retrieval(top_k=8)  # wider than the agent's default, to reduce false "unsupported"
ORDER = ["supported", "partial", "unsupported"]


def _ask(llm: LLM, topic: Topic, chunks: list[Chunk]) -> tuple[Groundability, list[str]]:
    """One verdict, then the quote check that can only make it stricter."""
    asked = {"id": topic.id, "topic": topic.topic, "example_question": topic.example_question}
    if "arithmetic" in topic.capabilities:  # small checkers call a topic unsupported because no chunk states the sum
        asked["note"] = "A calculator is available. The chunks need to give the input numbers, not the result."
    reply = llm.ask("02_groundability", {
        "topic_json": asked,
        "chunks_json": [c.model_dump() for c in chunks]}, Groundability, "groundability")
    if reply is None:
        return Groundability(verdict="unsupported", missing="the checker returned no usable verdict"), []
    texts = {c.chunk_id: c.text for c in chunks}
    log, good = [], []
    for item in reply.evidence:
        if item.chunk_id in texts and quote_in(item.quote, texts[item.chunk_id]):
            good.append(item)
        else:
            log.append(f"quote not found in {item.chunk_id}: {item.quote[:80]!r}")
    if reply.verdict != "unsupported":
        if not good:
            reply.verdict = "unsupported"  # support cannot be claimed without text
        elif log:
            reply.verdict = ORDER[ORDER.index(reply.verdict) + 1]
    reply.evidence = good
    return reply, log


def _other_values(index, chunks: list[Chunk]) -> list[Chunk]:
    """The nearest rows can all share one value ("only one supplier"): add a row for each other value of a short column."""
    extra = []
    for doc in index.docs:
        if not doc.records:
            continue
        rows = [c for c in index.chunks(WIDE) if c.doc == doc.name]  # one per record, in order
        shown = {c.chunk_id for c in chunks}
        hit = [i for i, row in enumerate(rows) if row.chunk_id in shown]
        if not hit:
            continue
        for column in doc.columns:
            values = list(dict.fromkeys(r[column] for r in doc.records))
            if len(values) > 10:
                continue
            for value in values:
                if all(doc.records[i][column] != value for i in hit):
                    hit.append(next(i for i, r in enumerate(doc.records) if r[column] == value))
                    extra.append(rows[hit[-1]])
    return chunks + extra


def _named_row(index, topic: Topic, chunks: list[Chunk]) -> Chunk | None:
    """A retrieved table row listing an item the question names. Small checkers deny prices that sit in such rows."""
    if not {"lookup_rows", "arithmetic"} & set(topic.capabilities):
        return None
    tables = {d.name for d in index.docs if d.records}
    question = topic.example_question.lower()
    for chunk in chunks:
        if chunk.doc in tables:
            for field in chunk.text.split("; "):
                item = field.split(": ", 1)[-1].split(",")[0].strip().lower()
                if len(item) >= 4 and re.search("[a-z]", item) and re.search(rf"\b{re.escape(item)}s?\b", question):
                    return chunk
    return None


def check(llm: LLM, index, topic: Topic) -> dict:
    record = {"topic_id": topic.id, "topic": topic.topic, "flagged": False, "log": []}
    if "live_weather" in topic.capabilities:  # no document can hold a live forecast
        return {**record, "verdict": "supported", "evidence": [], "missing": "", "log": ["answered by a live tool"]}
    chunks = index.search(f"{topic.topic}. {topic.example_question}", WIDE)
    if not chunks:
        return {**record, "verdict": "unsupported", "evidence": [], "missing": "no readable document text"}
    chunks = _other_values(index, chunks)
    reply, log = _ask(llm, topic, chunks)
    if reply.confidence == "low":
        again, more = _ask(llm, topic, chunks[::-1])
        log += more
        if again.verdict != reply.verdict:
            record["flagged"] = True
            reply = max(reply, again, key=lambda r: ORDER.index(r.verdict))
    row = _named_row(index, topic, chunks) if reply.verdict == "unsupported" else None
    if row:
        log.append(f"overruled by code: the checker said unsupported ({reply.missing}), "
                   f"but {row.chunk_id} lists an item the question names")
        return {**record, "verdict": "supported", "missing": "", "log": log, "flagged": True,
                "evidence": [{"chunk_id": row.chunk_id, "quote": row.text}]}
    return {**record, "verdict": reply.verdict, "missing": reply.missing, "log": log,
            "evidence": [e.model_dump() for e in reply.evidence]}


def apply(llm: LLM, index, requirements: Requirements) -> tuple[Requirements, list[dict], bool]:
    """Return (final requirements, verdict table, whether to stop the run)."""
    table = parallel(llm, lambda t: check(llm, index, t), requirements.must_answer)
    final = requirements.model_copy(deep=True)
    keep = []
    for topic, row in zip(final.must_answer, table):
        if row["verdict"] == "unsupported":
            final.must_refuse.append(RefuseTopic(
                id=f"X{len(final.must_refuse) + 1}", topic=topic.topic,
                reason=f"The documents do not cover this. {row['missing']}".strip()))
        else:
            if row["verdict"] == "partial":
                topic.scope_note = row["missing"]
            keep.append(topic)
    unsupported = len(table) - len(keep)
    final.must_answer = keep
    return final, table, not keep or unsupported > len(table) / 2
