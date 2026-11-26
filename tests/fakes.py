"""A scripted model and a hashing embedder, so the whole factory runs offline in tests."""

import hashlib
import json
import re

import numpy as np

from forge.index import tokenize

BRIEF = "I need an assistant that answers library members' questions about loans and late fees."
POLICY = """# Loan periods

DVDs are loaned for 7 days. A DVD can be renewed once.

Books are loaned for 21 days and a member may borrow up to 12 items at a time.

# Late fees

The late fee for a DVD is 2 pounds per day. Lost cards must be reported at the front desk.
Members who return items late receive a reminder by email after the due date has passed.
"""
FEES = "item_type,daily_fee,currency\n" + "".join(
    f"{item},{n}.25,GBP\n" for n, item in enumerate(
        "DVD Book CD Map Game Atlas Tablet Camera Journal Score Poster Kit".split(), 1))
FIX = "State each relevant sentence in full."


def embed(texts):
    vectors = np.zeros((len(texts), 256), np.float32)
    for row, text in enumerate(texts):
        for token in tokenize(text):
            vectors[row, int(hashlib.md5(token.encode()).hexdigest(), 16) % 256] += 1
    return vectors / np.clip(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9, None)


def _after(prompt: str, marker: str):
    """Decode the JSON value that follows the last occurrence of a marker."""
    rest = prompt[prompt.rindex(marker) + len(marker) :].lstrip()
    return json.JSONDecoder().raw_decode(rest)[0]


def _first_sentence(text: str) -> str:
    return re.split(r"(?<=\.)\s", text.split("\n")[-1] if text.startswith("#") else text)[0].strip("# ")


def _judge(prompt: str) -> dict:
    answer = prompt[prompt.rindex("ANSWER: ") + 8 : prompt.rindex("\nOUTPUT:")]
    evidence = _after(prompt, "EVIDENCE: ")
    facts = _after(prompt, "KEY_FACTS: ")
    refusal = "can't" in answer.lower()
    claims = []
    for sentence in [] if refusal else re.split(r"(?<=\.)\s+", answer):
        found = next((e["id"] for e in evidence if sentence.rstrip(".").lower() in e["text"].lower()), None)
        claims.append({"claim": sentence, "verdict": "supported" if found else "unsupported", "evidence_id": found})
    return {"claims": claims, "is_refusal": refusal, "asks_clarification": False,
            "key_facts": [{"id": f["id"], "verdict": "present" if f["fact"] in answer else "absent"}
                          for f in facts]}


def reply(prompt: str, question_log: list) -> dict:
    if prompt.startswith("You are the intake interviewer"):
        return {"questions": [
            {"id": "Q1", "question": "Should fine disputes be refused?", "why_it_matters": "scope",
             "trigger": "late fees", "default_answer": "Yes, refuse them."},
            {"id": "Q2", "question": "Invented?", "why_it_matters": "x", "trigger": "not in the brief",
             "default_answer": "No."}]}
    if prompt.startswith("You turn a brief"):
        return {"scope": "Loans and fees.", "audience": "Library members", "tone": "short and plain",
                "must_answer": [{"id": "T1", "topic": "Loan periods", "example_question": "How long is a DVD loan?",
                                 "capabilities": ["retrieval"]},
                                {"id": "T2", "topic": "Late fees", "example_question": "What is the DVD late fee?",
                                 "capabilities": ["retrieval"]}],
                "must_refuse": [{"id": "X1", "topic": "Fine disputes", "reason": "excluded", "referral": "the desk"}],
                "assumptions": []}
    if prompt.startswith("You check whether a set of document chunks"):
        topic, chunks = _after(prompt, "TOPIC: "), _after(prompt, "CHUNKS: ")
        if topic["id"] == "Q":  # the answerability gate
            return {"topic_id": "Q", "verdict": "unsupported", "evidence": [], "missing": "x", "confidence": "high"}
        return {"topic_id": topic["id"], "verdict": "supported", "missing": "", "confidence": "high",
                "evidence": [{"chunk_id": chunks[0]["chunk_id"], "quote": chunks[0]["text"][:60]}]}
    if prompt.startswith("You write the instructions"):
        sections = ["role", "scope", "audience_and_tone", "grounding_rules", "refusal_policy",
                    "clarification_policy", "citation_rules", "tool_rules", "conflict_policy"]
        return {"name": "Library Helper", "system_prompt": {s: f"1. Rule for {s}." for s in sections},
                "tools": [{"name": "marine_weather", "topic_ids": ["T1"], "why": "not needed"}],
                "refusal_message": "I can't find that."}
    if prompt.startswith("You write test questions"):
        category = re.search(r"\nCATEGORY: (\w+)", prompt).group(1)
        chunks = _after(prompt, "\nCHUNKS: ")
        cases = []
        for _ in range(2):
            question_log.append(1)
            n = len(question_log)
            # unique tokens defeat dedup; the chunk's own words let retrieval find it
            question = (f"zeta{n} kappa{n * 7} omega{n * 13} sigma{n * 17} theta{n * 19} "
                        f"{_first_sentence(chunks[0]['text'])}?")
            if category == "must_refuse":
                cases.append({"question": question, "expected_behavior": "refuse", "key_facts": [],
                              "near_chunk_id": chunks[0]["chunk_id"]})
                continue
            facts = [{"fact": _first_sentence(c["text"]), "quote": _first_sentence(c["text"]),
                      "chunk_id": c["chunk_id"]} for c in chunks]
            cases.append({"question": question,
                          "expected_behavior": "clarify" if category == "ambiguous" else "answer",
                          "key_facts": facts, "source_chunk_ids": [c["chunk_id"] for c in chunks]})
        return {"cases": cases}
    if prompt.startswith("You check an assistant's answer"):
        return _judge(prompt)
    if prompt.startswith("You diagnose"):
        return {"category": "prompt_defect", "subtype": "missed_key_fact",
                "fix_target": "/system_prompt/grounding_rules", "evidence": "e", "hypothesis": "h"}
    if prompt.startswith("You fix an assistant"):
        allowed = _after(prompt, "ALLOWED_PATHS: ")
        path = next((p for p in allowed if p.startswith("/system_prompt/")), None)
        op = ({"op": "append_rule", "path": path, "value": FIX} if path
              else {"op": "set", "path": "/retrieval/top_k", "value": 7})
        return {"rationale": "answer when the text is there", "addresses": [], "expected_effect": "", "risk": "",
                "ops": [op]}
    if prompt.startswith("You write the prose sections"):
        failures = _after(prompt, "FAILURES: ")
        return {"summary": "Sealed result: [[held_out.final]].",
                "what_still_fails": " ".join(f["id"] for f in failures) or "None.",
                "why_by_category": "Shared causes.", "pipeline_doubts": "Judge: [[judge.canaries]].",
                "next_fixes": "A general change."}
    raise AssertionError(f"unexpected prompt: {prompt[:120]}")


def make_transport():
    question_log: list = []

    def transport(side, messages, temperature, max_tokens):
        system = messages[0]["content"]
        # the agent: quote the top chunk; until it is patched, refuse odd-numbered questions
        if messages[0]["role"] == "system":
            user = messages[1]["content"]
            number = int(re.search(r"zeta(\d+)", user).group(1)) if "zeta" in user else 0
            found = re.search(r"\[([^\]]+)\] \(file: [^)]+\)\n(.+)", user)
            if (number % 2 and FIX not in system) or not found:
                out = {"status": "refused", "answer": "I can't find that."}
            else:
                sentence = _first_sentence(found.group(2))
                out = {"status": "answered", "answer": sentence,
                       "citations": [{"chunk_id": found.group(1), "quote": sentence}]}
        else:
            out = reply(system, question_log)
        return json.dumps(out), 10, 10

    return transport
