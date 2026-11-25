"""Deterministic checks: everything code can decide, before any judge is asked."""

import re
import unicodedata
from difflib import SequenceMatcher

from rapidfuzz import fuzz

from .schemas import AgentDef, Case, Chunk, KeyFact, Turn

NUMBER = re.compile(r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).translate(PUNCT).lower().split())


def numbers(text: str) -> set[float]:
    return {float(n.replace(",", "")) for n in NUMBER.findall(text)}


def ngrams(text: str, n: int) -> set[tuple]:
    words = re.findall(r"\w+", normalize(text))
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def quote_in(quote: str, text: str, threshold: float = 0.9) -> bool:
    q, t = normalize(quote), normalize(text)
    if not q or len(q) > len(t) * 1.1:  # partial_ratio would otherwise match a short text inside a long quote
        return False
    if not numbers(q) <= numbers(t):  # one changed digit still scores above 0.9 on a long sentence
        return False
    return fuzz.partial_ratio(q, t) >= threshold * 100


# --- gold evidence (matched by quote, so it survives re-chunking) ---


def quoted(case: Case) -> list[KeyFact]:
    return [f for f in case.key_facts if f.quote]


def _holds(case: Case, fact: KeyFact, chunk: Chunk) -> bool:
    doc = next((c.doc for c in case.source_chunks if c.chunk_id == fact.chunk_id), None)
    return (doc is None or chunk.doc == doc) and quote_in(fact.quote, chunk.text)


def gold_in(case: Case, chunks: list[Chunk]) -> bool | None:
    facts = quoted(case)
    if not facts:
        return None
    return all(any(_holds(case, f, c) for c in chunks) for f in facts)


def gold_rank(case: Case, ranked: list[Chunk]) -> int | None:
    """The rank by which every gold quote has appeared."""
    worst = 0
    for fact in quoted(case):
        rank = next((i for i, c in enumerate(ranked, 1) if _holds(case, fact, c)), None)
        if rank is None:
            return None
        worst = max(worst, rank)
    return worst or None


# --- hard checks 1-4 and 8, soft checks 5 and 6 ---

ALLOWED_STATUS = {"answer": {"answered"}, "refuse": {"refused"}, "clarify": {"needs_clarification", "answered"}}


def context_chunks(turn: Turn) -> list[Chunk]:
    return turn.retrieved + [c for call in turn.tool_calls for c in call.chunks]


def hard_checks(case: Case, turn: Turn, agent: AgentDef) -> list[str]:
    """Reasons for a hard failure. Empty means the checks pass."""
    failures = []
    if not turn.contract_valid:
        return ["check 1: the reply did not match the output contract"]
    if turn.status not in ALLOWED_STATUS[case.expected_behavior]:
        failures.append(f"check 2: expected to {case.expected_behavior}, status was {turn.status}")
    texts: dict[str, str] = {}
    for chunk in context_chunks(turn):
        texts[chunk.chunk_id] = texts.get(chunk.chunk_id, "") + " " + chunk.text
    for citation in turn.citations:
        if citation.chunk_id not in texts:
            failures.append(f"check 3: cited {citation.chunk_id}, which was not in the context")
        elif not quote_in(citation.quote, texts[citation.chunk_id], 0.85):
            failures.append(f"check 4: quote not found in {citation.chunk_id}: {citation.quote[:80]!r}")
    attached = {t.name for t in agent.tools}
    used = {c.name for c in turn.tool_calls if c.ok}
    failures += [f"check 8: expected tool {t} was not called" for t in case.expected_tools if t not in used]
    failures += [f"check 8: called unattached tool {c.name}" for c in turn.tool_calls if c.name not in attached]
    return failures


def strip_citations(turn: Turn) -> str:
    """The answer as the judge sees it: no chunk ids, no list numbering."""
    text = re.sub(r"\[C\d+\]", "", turn.text)  # the prompt labels of runtime.run_turn
    for chunk_id in {c.chunk_id for c in context_chunks(turn)} | {c.chunk_id for c in turn.citations}:
        text = text.replace(f"[{chunk_id}]", "").replace(chunk_id, "")
    return text.strip()


def number_flag(case: Case, turn: Turn) -> bool:
    """True if the answer states a number found in no context, tool output or question."""
    if turn.status == "refused":
        return False
    answer = re.sub(r"(?m)^\s*\d+[.)]\s", "", strip_citations(turn))
    seen = " ".join([case.question] + [c.text for c in context_chunks(turn)]
                    + [c.result for c in turn.tool_calls if c.ok])
    return bool(numbers(answer) - numbers(seen))


def facts_hit(case: Case, answer: str) -> set[str]:
    """Key facts stated word for word, so no judge is needed for them."""
    text = normalize(answer)
    return {f.id for f in case.key_facts
            if any(s and normalize(s).rstrip(".") in text for s in (f.fact, f.quote))}


# --- sentence marks for the UI: where each sentence of an answer came from ---

WORD = re.compile(r"[^\W_]+")  # splits CSV field names such as unit_price
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])|\n+")


def split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in SENTENCE_END.split(text)]
    return [s for s in parts if s and not re.fullmatch(r"\(?\d+[.)]?", s)]  # bare list markers such as "2."


def sentence_support(sentence: str, chunks: list[Chunk]) -> tuple[str, Chunk | None, str]:
    """("quoted" | "close" | "none" | "short", chunk, matched words). Code decides, no model.

    quoted: 6+ consecutive words appear in one chunk. close: half the content words appear in one
    chunk. Either way every number in the sentence must appear in that chunk.
    Note: thresholds are starting values, not calibrated against hand labels.
    """
    words = WORD.findall(normalize(sentence))
    if len(words) < 5:
        return "short", None, ""
    content = {w for w in words if len(w) > 3}
    best = ("none", None, "")
    for chunk in chunks:
        if not numbers(sentence) <= numbers(chunk.text):
            continue
        cwords = WORD.findall(normalize(chunk.text))
        run = SequenceMatcher(None, words, cwords, autojunk=False).find_longest_match()
        if run.size >= 6:
            return "quoted", chunk, " ".join(words[run.a : run.a + run.size])
        if best[0] == "none" and content and len(content & set(cwords)) * 2 >= len(content):
            best = ("close", chunk, "")
    return best
