"""The intake interviewer: at most 5 questions, every default recorded as an assumption."""

import re
import select
import sys

from .inventory import Doc, summary
from .llm import LLM
from .schemas import CAPABILITIES, Assumption, Question, Questions, Requirements, Topic

MAX_QUESTIONS = 5
TIMEOUT_SECONDS = 60
FILLER = {"a", "an", "the", "of", "in", "on", "and", "or", "for", "to", "about", "any", "question"}
EXCLUDES = re.compile(r"\b(not|never|no|refuse|decline|except|excluding|exclude|without|don't)\b", re.I)
IDENTIFIER = re.compile(r"\b(?=[A-Za-z0-9-]*\d)(?=[A-Za-z0-9-]*[A-Z])[A-Za-z0-9-]{4,}\b")
SUMS = re.compile(r"(?i)\b(totals?|calculat\w*|comput\w*|sum|add\w* up|work\w* out|differences?|percent\w*|"
                  r"averages?|pro[- ]?rata)\b")  # a brief asks for computed answers in words like these
PLACEHOLDER = re.compile(r"\b\d{4,}\b(?!\s*(?:units?|pieces?|EUR|USD))")  # "the 5678 pump", not "5000 units"


def _flat(text: str) -> str:
    return " ".join(text.lower().split())


def _words(text: str) -> set[str]:
    return {w.rstrip("s") if len(w) > 3 else w for w in re.findall(r"[a-z0-9]+", text.lower())} - FILLER


def asked_for(topic: str, brief: str, docs: list[Doc], record: list[dict]) -> bool:
    """True if a refusal touches what the brief asks about and no person chose to exclude it."""
    for doc in docs:
        topic = re.sub(re.escape(doc.name), " ", topic, flags=re.I)
    wanted = _words(topic) & _words(brief)
    if not wanted:
        return False
    excluded = any(wanted & _words(s) and EXCLUDES.search(s) for s in re.split(r"(?<=[.!?;])\s+", brief))
    chosen = any(a["source"] == "requester" and wanted & _words(f"{a['question']} {a['answer']}") for a in record)
    return not excluded and not chosen


def _overrule(reply: Requirements, brief: str, docs: list[Doc], record: list[dict]) -> None:
    """A default nobody confirmed may not refuse what the brief asks about: the documents decide.

    The topic moves to must_answer, where the groundability guard keeps it or demotes it again.
    """
    dropped = [r for r in reply.must_refuse if asked_for(r.topic, brief, docs, record)]
    reply.must_refuse = [r for r in reply.must_refuse if r not in dropped]
    for refusal in dropped:
        name = re.sub(r"\(.*?\)|\*", "", refusal.topic).strip() or refusal.topic
        reply.must_answer.append(Topic(id="", topic=name, example_question=name))
        stale = {a["id"] for a in record if a["source"] == "default" and "refus" in a["answer"].lower()
                 and _words(refusal.topic) & _words(f"{a['question']} {a['answer']}")}
        reply.assumptions = [a for a in reply.assumptions if a.from_question not in stale]
        reply.assumptions.append(Assumption(
            text=f"Overruled by code: nobody confirmed refusing '{refusal.topic}', and the brief asks about it, so "
            "the documents decide (see the groundability table).", from_question=", ".join(sorted(stale))))


def _real_examples(topics: list[Topic], brief: str, docs: list[Doc]) -> None:
    """A small model invents identifiers ("P12345"). The groundability guard then searches for one and refuses the topic."""
    texts = [brief, *(s.text for d in docs for s in d.segments), *(v for d in docs for r in d.records for v in r.values())]
    known = "\n".join(texts).lower()
    real = next(((d, k, v) for d in docs for r in d.records[:1] for k, v in r.items() if IDENTIFIER.fullmatch(v)), None)
    for topic in topics:
        invented = [t for t in IDENTIFIER.findall(topic.example_question) if t.lower() not in known]
        invented += [n for n in PLACEHOLDER.findall(topic.example_question) if not re.search(rf"\b{n}\b", known)]
        if invented and real:  # swapping only the code left nonsense: a pump seal as "the engine from Gulfstream"
            doc, key, value = real
            topic.example_question = f"What are the {', '.join(c for c in doc.columns if c != key)} for {key} {value}?"
        elif invented:
            topic.example_question = topic.topic


def questions(llm: LLM, brief: str, docs: list[Doc], embed) -> tuple[list[Question], list[dict]]:
    """Return (questions to ask, questions dropped by code with the reason)."""
    reply = llm.ask("01a_intake_questions",
                    {"max_questions": MAX_QUESTIONS, "brief": brief, "inventory_json": summary(docs)},
                    Questions, "intake")
    asked = reply.questions[:MAX_QUESTIONS] if reply else []
    names = {_flat(d.name) for d in docs}
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", brief.strip()) if s]
    brief_vectors = embed(sentences) if asked and sentences else None
    kept, dropped = [], []
    for question in asked:
        trigger = _flat(question.trigger)
        if not trigger or (trigger not in _flat(brief) and trigger not in names):
            dropped.append({"question": question.question, "reason": "trigger is not in the brief or a file name"})
        elif brief_vectors is not None and (brief_vectors @ embed([question.question])[0]).max() > 0.9:
            dropped.append({"question": question.question, "reason": "the brief already answers it"})
        else:
            question.id = f"Q{len(kept) + 1}"
            kept.append(question)
    return kept, dropped


def _read_line(timeout: int) -> str | None:
    ready, _, _ = select.select([sys.stdin], [], [], timeout)  # POSIX only
    line = sys.stdin.readline() if ready else ""
    return line.strip() if line else None


def interview(asked: list[Question], unattended: bool, answers: dict | None = None) -> list[dict]:
    record = []
    for q in asked:
        answer, source = q.default_answer, "default"
        if answers and q.id in answers:
            answer, source = str(answers[q.id]), "requester"
        elif not unattended:
            print(f"\n{q.id}. {q.question}\n    why: {q.why_it_matters}\n    Enter accepts: {q.default_answer}\n> ",
                  end="", flush=True)
            typed = _read_line(TIMEOUT_SECONDS)
            if typed is not None:  # a bare Enter is a person accepting the default
                answer, source = typed or q.default_answer, "requester"
        record.append({"id": q.id, "question": q.question, "answer": answer, "source": source})
    return record


def requirements(llm: LLM, brief: str, docs: list[Doc], record: list[dict]) -> Requirements:
    reply = llm.ask("01b_requirements", {
        "brief": brief, "inventory_json": summary(docs), "interview_json": record,
        "capabilities_json": list(CAPABILITIES)}, Requirements, "intake")
    if reply is None or not reply.must_answer:
        reply = Requirements(
            scope=brief, audience="the people named in the brief", tone="plain and short",
            must_answer=[Topic(id="T1", topic=brief, example_question=brief)],
            assumptions=[Assumption(text="The requirements writer failed; the whole brief is treated as one topic.")])
    covered = {a.from_question for a in reply.assumptions}
    reply.assumptions += [
        Assumption(text=f"{a['question']} Assumed: {a['answer']}", from_question=a["id"])
        for a in record if a["source"] == "default" and a["id"] not in covered]
    _overrule(reply, brief, docs, record)
    _real_examples(reply.must_answer, brief, docs)
    for n, topic in enumerate(reply.must_answer, 1):
        topic.id = f"T{n}"
        wanted = ["retrieval"] + [c for c in topic.capabilities if c in CAPABILITIES]
        if not SUMS.search(brief):  # small models tag any topic with a number as arithmetic
            wanted = [c for c in wanted if c != "arithmetic"]
        topic.capabilities = list(dict.fromkeys(wanted))
    for n, topic in enumerate(reply.must_refuse, 1):
        topic.id = f"X{n}"
    return reply
