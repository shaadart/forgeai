"""Code gates on generated cases: the test writer is the same class of weak model as everything else."""

from . import groundability
from .checks import ngrams, numbers, quote_in
from .llm import LLM
from .schemas import Case, Chunk, RawCase, Topic
from .tools import calculator

EXPECTED = {"answerable": "answer", "must_refuse": "refuse", "ambiguous": "clarify",
            "cross_document": "answer", "tool": "answer"}
DUPLICATE_COSINE = 0.92


class Rejected(ValueError):
    def __init__(self, gate: str, reason: str):
        super().__init__(reason)
        self.gate = gate


def build_case(raw: RawCase, category: str, chunks: list[Chunk], tools: list[str]) -> Case:
    """Schema, quote, derived, tool and cross-document gates. No model calls."""
    if raw.expected_behavior != EXPECTED[category]:
        raise Rejected("schema", f"a {category} case must expect {EXPECTED[category]}")
    if not raw.question.strip():
        raise Rejected("schema", "empty question")
    given = {c.chunk_id: c for c in chunks}
    facts = [] if category == "must_refuse" else raw.key_facts
    used: list[str] = []
    if category != "must_refuse" and not facts:
        raise Rejected("schema", "no key facts")
    for n, fact in enumerate(facts, 1):
        fact.id = f"K{n}"
        if fact.derived:
            fact.quote = fact.chunk_id = None
            try:
                value = calculator.evaluate(fact.derived)
            except (ValueError, SyntaxError, ZeroDivisionError, TypeError, OverflowError) as e:
                raise Rejected("derived", f"{fact.derived!r} does not evaluate: {e}") from e
            if not any(abs(value - x) < 0.01 for x in numbers(fact.fact)):
                raise Rejected("derived", f"{fact.derived!r} = {value}, which the fact does not state")
        elif not fact.quote or fact.chunk_id not in given:
            raise Rejected("quote_check", f"fact has no quote from a given chunk: {fact.fact[:80]}")
        elif not quote_in(fact.quote, given[fact.chunk_id].text):
            raise Rejected("quote_check", f"quote not in {fact.chunk_id}: {fact.quote[:80]!r}")
        else:
            used.append(fact.chunk_id)
    if facts and not used:
        raise Rejected("quote_check", "no quoted fact")

    if category == "must_refuse":
        near = raw.near_chunk_id if raw.near_chunk_id in given else chunks[0].chunk_id
        used = [near]
    else:
        used += [i for i in raw.source_chunk_ids if i in given]
    sources = [given[i] for i in dict.fromkeys(used)]
    if category == "ambiguous" and len({f.chunk_id for f in facts if f.quote}) < 2:
        raise Rejected("schema", "an ambiguous case needs quoted facts from two chunks")
    if category == "cross_document":
        quotes = [f.quote for f in facts if f.quote]
        if len({c.doc for c in sources}) < 2 or any(all(quote_in(q, c.text) for q in quotes) for c in sources):
            category = "answerable"  # one chunk is enough, so it is not cross-document
    expected_tools = [t for t in raw.expected_tools if t in tools] if category == "tool" else []
    if category == "tool" and not expected_tools:
        raise Rejected("schema", "a tool case names no attached tool")

    overlap = any(ngrams(raw.question, 5) & ngrams(c.text, 5) for c in sources)
    return Case(id="", category=category, question=raw.question.strip(), expected_behavior=raw.expected_behavior,
                key_facts=facts, source_chunks=sources, expected_tools=expected_tools,
                why_unanswerable=raw.why_unanswerable, flags=["lexical_overlap"] if overlap else [])


def check_duplicate(case_vector, kept: list[Case], vectors: list) -> None:
    for other, seen in zip(kept, vectors):
        if float(case_vector @ seen) > DUPLICATE_COSINE:
            raise Rejected("dedup", f"near-duplicate of: {other.question}")


def check_answerability(llm: LLM, index, case: Case) -> None:
    """A must-refuse question the documents answer is a wrong test."""
    if case.expected_behavior == "refuse":
        probe = Topic(id="Q", topic=case.question, example_question=case.question)
        row = groundability.check(llm, index, probe)
        if row["verdict"] != "unsupported":  # partly answerable is not a clean test of refusal
            raise Rejected("answerability", f"the documents answer this must-refuse question ({row['verdict']})")
