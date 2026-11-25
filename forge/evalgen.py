"""Generate the eval set from the documents themselves, with quotas per category."""

import random

from pydantic import ValidationError

from . import gates
from .llm import LLM, fill, load_prompt
from .loop import parallel
from .schemas import AgentDef, Case, Chunk, RawCase, RawCases, Requirements, Retrieval

QUOTAS = {"answerable": 18, "must_refuse": 10, "ambiguous": 4, "cross_document": 4, "tool": 4}
PER_CALL = 2
TARGET_KEPT = 24  # top up until this many survive; the floor required is MINIMUM
MINIMUM = 20
ROUNDS = 3


def chunk_pool(index, req: Requirements) -> list[Chunk]:
    """Chunks near the supported topics, interleaved so that every topic is covered early."""
    wide = Retrieval(top_k=12)
    ranked = [index.search(f"{t.topic}. {t.example_question}", wide) for t in req.must_answer]
    pool = [r[i] for i in range(wide.top_k) for r in ranked if i < len(r)]
    return list({c.chunk_id: c for c in pool}.values())


def _jobs(pool: list[Chunk], index, agent: AgentDef, rng: random.Random, round_n: int) -> list[tuple]:
    """(category, chunks) for one round. Later rounds only top up the two big categories."""
    shuffled = rng.sample(pool, len(pool))
    vectors = index.embed([c.text for c in shuffled])
    similarity = vectors @ vectors.T

    def nearest(i, other_doc: bool):
        order = sorted(range(len(shuffled)), key=lambda j: -similarity[i, j])
        return next((shuffled[j] for j in order if shuffled[j].text != shuffled[i].text
                     and (shuffled[j].doc != shuffled[i].doc) == other_doc), None)

    jobs = []
    for category, quota in QUOTAS.items():
        if round_n and category not in ("answerable", "must_refuse"):
            continue
        if category == "tool" and not agent.tools:
            continue
        tables = [c for c in shuffled if c.doc.lower().endswith(".csv")]
        for n in range((quota if not round_n else quota // 2) // PER_CALL):
            i = (n * 3 + round_n) % len(shuffled)
            if category in ("answerable", "must_refuse"):
                jobs.append((category, [shuffled[(n + round_n * 9) % len(shuffled)]]))
            elif category == "tool":
                source = tables or shuffled
                jobs.append((category, [source[n % len(source)]]))
            else:
                # ambiguous: two similar chunks, preferably from one file; cross_document: two files
                partner = nearest(i, category == "cross_document")
                if partner is None and category == "ambiguous":
                    partner = nearest(i, True)
                if partner:
                    jobs.append((category, [shuffled[i], partner]))
    return jobs


def _generate(llm: LLM, req: Requirements, agent: AgentDef, job: tuple, sample: int) -> list[dict]:
    category, chunks = job
    meta, blocks = load_prompt("04_evalgen")
    values = {"audience": req.audience, "n": PER_CALL, "chunks_json": [c.model_dump() for c in chunks],
              "must_refuse_topics": [t.topic for t in req.must_refuse], "tools": [t.name for t in agent.tools]}
    values["category_block"] = fill(blocks[category], values)
    reply = llm.parsed(meta["side"], [{"role": "user", "content": fill(blocks[""], values)}],
                       float(meta["temperature"]), RawCases, "evalgen", sample)
    return reply.cases[: PER_CALL * 2] if reply else []


def build(llm: LLM, index, req: Requirements, agent: AgentDef, seed: int = 7) -> tuple[list[Case], list[dict], dict]:
    """Return (kept cases, rejected cases with the gate, stats)."""
    pool = chunk_pool(index, req)
    kept: list[Case] = []
    vectors: list = []
    rejected: list[dict] = []
    disagreements: list[str] = []
    tools = [t.name for t in agent.tools]
    rng = random.Random(seed)
    sample = 0
    for round_n in range(ROUNDS if pool else 0):
        if round_n and len(kept) >= TARGET_KEPT:
            break
        jobs = _jobs(pool, index, agent, rng, round_n)
        numbered = list(enumerate(jobs, sample))
        sample += len(jobs)
        replies = parallel(llm, lambda item: _generate(llm, req, agent, item[1], item[0]), numbered)
        candidates: list[tuple] = []  # (case, vector, raw) past the code gates and dedup
        for (category, chunks), raws in zip(jobs, replies):
            for raw in raws:
                try:
                    try:
                        parsed = RawCase.model_validate(raw)
                    except ValidationError as e:
                        raise gates.Rejected("schema", str(e)[:200]) from e
                    case = gates.build_case(parsed, category, chunks, tools)
                    vector = index.embed([case.question])[0]
                    gates.check_duplicate(vector, kept + [c[0] for c in candidates], vectors + [c[1] for c in candidates])
                except gates.Rejected as e:
                    rejected.append({"gate": e.gate, "reason": str(e), "category": category, "case": raw})
                    continue
                candidates.append((case, vector, raw))

        def answerability(item):
            try:
                gates.check_answerability(llm, index, item[0])
            except gates.Rejected as e:
                return e

        for (case, vector, raw), error in zip(candidates, parallel(llm, answerability, candidates)):
            if error:
                rejected.append({"gate": error.gate, "reason": str(error), "category": case.category, "case": raw})
                disagreements.append(case.question)
                continue
            case.id = f"C{len(kept) + 1:02d}"
            kept.append(case)
            vectors.append(vector)
    overlap = sum("lexical_overlap" in c.flags for c in kept)
    stats = {"generated": len(kept) + len(rejected), "kept": len(kept), "rejected": len(rejected),
             "lexical_overlap": overlap, "groundability_disagreements": disagreements,
             "below_minimum": len(kept) < MINIMUM}
    return kept, rejected, stats
