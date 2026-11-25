"""Planted answers the judge must grade correctly on every run. Built by code; no LLM writes them."""

import re

from . import checks
from .judge import label, outcome
from .llm import LLM
from .schemas import Case, Chunk

PLANTED = "Written approval from the regional supervisor is also required before this applies."
REFUSAL = "I can't find that in the documents. Please ask the responsible person."


def _sentence(text: str) -> str | None:
    """A whole sentence if there is one: a fragment or a heading is not a "true sentence" to pad with."""
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text)]
    parts = [s for s in parts if 6 <= len(s.split()) <= 40 and "#" not in s]
    return next((s for s in parts if s[0].isupper() and s.endswith(".")), parts[0] if parts else None)


def _swap_digit(text: str, facts: str = "") -> str:
    """Change the first digit of one number, everywhere it appears. A number a key fact states is preferred:
    the judge may fold a repeated sentence into one claim and never state a cross-reference such as "paragraph 6"."""
    number = (checks.NUMBER.search(facts) or checks.NUMBER.search(text)).group()
    changed = str(int(number[0]) % 9 + 1) + number[1:]
    return re.sub(rf"(?<![\w.]){re.escape(number)}(?![\d])", changed, text)


def run(llm: LLM, cases: list[Case], chunks: list[Chunk]) -> list[dict]:
    results = []

    def add(name, ok, detail=""):
        results.append({"name": name, "ok": bool(ok), "detail": detail})

    # a gold case whose facts add no number that its quotes do not show; one with a number is preferred
    usable = [c for c in cases if c.expected_behavior == "answer" and c.source_chunks and checks.quoted(c)
              and all(checks.numbers(f.fact) <= checks.numbers(f.quote) for f in checks.quoted(c))]
    usable.sort(key=lambda c: not any(checks.numbers(f.fact) for f in checks.quoted(c)))
    if usable:
        case = usable[0]
        facts = [(f.id, f.fact) for f in checks.quoted(case)]
        ids = [i for i, _ in facts]
        source = {c.text for c in case.source_chunks}
        others = [c.text for c in chunks if c.text not in source and _sentence(c.text)][:3]
        evidence = [c.text for c in case.source_chunks] + others
        gold = " ".join(f"{part.rstrip('. ')}." for f in checks.quoted(case) for part in (f.fact, f.quote))

        def judged(answer, order=evidence):
            return label(llm, case.question, answer, order, facts)

        def clean(labels):
            return labels and all(c.verdict == "supported" for c in labels.claims)

        base = judged(gold)
        add("gold", clean(base) and all(v == "present" for v in outcome(base, ids)[2]))
        if checks.numbers(gold):
            swapped = judged(_swap_digit(gold, " ".join(fact for _, fact in facts)))
            # here and below either non-supported label fails the answer, which is what the canaries protect
            add("number_swap", swapped and any(c.verdict != "supported" for c in swapped.claims))
        if others:
            padded = judged(" ".join([gold] + [f"{_sentence(t).rstrip('. ')}." for t in others]))
            add("padded", clean(padded) and base and outcome(padded, ids)[2] == outcome(base, ids)[2])
        planted = judged(f"{gold} {PLANTED}")
        add("planted_claim", planted and any(c.verdict != "supported" for c in planted.claims))
        if len(evidence) > 1:
            shuffled = judged(gold, evidence[::-1])
            add("shuffled", shuffled and base and outcome(shuffled, ids) == outcome(base, ids))
    else:
        add("gold", False, "no usable answerable case to build canaries from")
    refusal = next((c for c in cases if c.expected_behavior == "refuse"), None)
    if refusal:
        labels = label(llm, refusal.question, REFUSAL, [c.text for c in refusal.source_chunks], [])
        add("correct_refusal", labels and labels.is_refusal)
    return results


def healthy(results: list[dict]) -> bool:
    return bool(results) and all(r["ok"] for r in results)
