"""The code checks that catch the pipeline lying."""

import pytest

from forge import generator, intake, judge, patch, report, split
from forge.checks import quote_in
from forge.classify import ALLOWED, attribute
from forge.llm import parse_json
from forge.inventory import Doc
from forge.schemas import AgentDef, Case, Chunk, GeneratedAgent, Labels, Patch, PatchOp, Prose, RawCases, Result, SECTIONS, Turn
from forge.tools import calculator, csv_lookup

SENTENCE = "Members who hold a standard card may keep a borrowed DVD for 14 days from the date of issue."


def test_quote_check_rejects_one_changed_digit_and_oversized_quotes():
    assert quote_in("may keep a borrowed  DVD for 14 days", SENTENCE)
    assert not quote_in(SENTENCE.replace("14", "74"), SENTENCE)
    assert not quote_in(SENTENCE + " and a good deal of invented text after it", SENTENCE)


def test_calculator_only_does_arithmetic():
    assert calculator.evaluate("round(2 * 4 * 1.5, 2)") == 12
    for bad in ("__import__('os')", "(1).__class__", "9**9**9", "'a' * 3", "open('x')"):
        with pytest.raises((ValueError, SyntaxError)):
            calculator.evaluate(bad)


def test_csv_lookup_filters_and_refuses_unknown_files():
    table = Doc(name="p.csv", type="csv", sha256="x", columns=["part", "price"],
                records=[{"part": "A-1", "price": "1,200"}, {"part": "A-2", "price": "90"}])
    text, chunks = csv_lookup.run([table], "p.csv", [{"column": "price", "op": "gt", "value": 100}])
    assert [c.chunk_id for c in chunks] == ["p.csv#row1"] and "A-1" in text
    with pytest.raises(ValueError):
        csv_lookup.run([table], "../../etc/passwd")


def _agent():
    return AgentDef(name="a", docs_dir=".", documents={}, refusal_message="no",
                    system_prompt={s: "1. Rule." for s in SECTIONS})


@pytest.mark.parametrize("op, reason", [
    (PatchOp(op="set", path="/retrieval/top_k", value=50), "outside"),
    (PatchOp(op="set", path="/name", value="x"), "not allowed"),
    (PatchOp(op="append_rule", path="/system_prompt/grounding_rules",
             value="Say the DVD loan period is 7 days."), "leakage"),
    (PatchOp(op="append_rule", path="/system_prompt/grounding_rules", value="word " * 61), "adds"),
    (PatchOp(op="replace_sentence", path="/system_prompt/refusal_policy", old="Fine disputes", new="x"),
     "removes"),
])
def test_patch_checks(op, reason):
    agent = _agent()
    agent.system_prompt["refusal_policy"] = "1. Refuse Fine disputes."
    allowed = ALLOWED["hallucination"] + ["/retrieval/top_k"]
    with pytest.raises(patch.PatchRejected, match=reason):
        patch.apply(agent, Patch(ops=[op]), allowed, ["The DVD loan period is 7 days."], [], ["Fine disputes"])


def test_patch_applies_and_rejected_patch_cannot_repeat():
    agent = _agent()
    change = Patch(ops=[PatchOp(op="set", path="/retrieval/bm25_weight", value=0.7)])
    new, changes = patch.apply(agent, change, ALLOWED["retrieval_miss"], [], [])
    assert new.retrieval.bm25_weight == 0.7 and new.version == 1 and changes[0]["from"] == 0.4
    with pytest.raises(patch.PatchRejected, match="repeats"):
        patch.apply(agent, change, ALLOWED["retrieval_miss"], [],
                    [{"ops": patch.signature(change), "accepted": False}])


def test_refusal_without_the_right_context_is_a_retrieval_miss():
    case = Case(id="T01", category="answerable", question="q", expected_behavior="answer")
    result = Result(case_id="T01", state="failed", gold_in_topk=False,
                    turn=Turn(status="refused", answer="no"))
    assert attribute(case, result, lambda: (True, True, ""))[0] == "retrieval_miss"
    assert attribute(case, result, lambda: (False, False, "x"))[0] == "eval_defect"


def test_split_keeps_one_paragraph_on_one_side():
    cases = [Case(id=f"C{i}", category="answerable", question=str(i), expected_behavior="answer",
                  source_chunks=[Chunk(chunk_id=f"d#{i // 2}", doc="d", text="t")]) for i in range(30)]
    train, sealed, _ = split.split(cases)
    assert 8 <= len(sealed) <= 11 and len(train) + len(sealed) == 30
    assert not {c.source_chunks[0].chunk_id for c in train} & {c.source_chunks[0].chunk_id for c in sealed}


def test_split_seals_every_category_even_when_groups_mix_them():
    kinds = ["answerable"] * 12 + ["must_refuse"] * 6 + ["cross_document"] * 3
    chunk = lambda i: Chunk(chunk_id=f"d#{i % 9}", doc="d", text="t")
    cases = [Case(id=f"C{i}", category=k, question=str(i), expected_behavior="answer", source_chunks=[chunk(i)])
             for i, k in enumerate(kinds)]
    _, sealed, _ = split.split(cases)
    assert {c.category for c in sealed} == set(kinds) and 5 <= len(sealed) <= 10


def test_report_writer_may_not_type_numbers_or_hide_failures():
    known = {"held_out.passed": "8"}

    def check(summary, failing="S03"):
        prose = Prose(summary=summary, what_still_fails=failing, why_by_category="x", pipeline_doubts="x",
                      next_fixes="x")
        return report.check_prose(prose, known, {"S03"})

    assert check("Passed [[held_out.passed]], 95% interval wide. See T11.") is None
    assert "digit" in check("Passed 8 cases.")
    assert "number word" in check("About half passed.")
    assert "unknown key" in check("[[made.up]]")
    assert "banned" in check("A robust agent.")
    assert "leaves out" in check("ok", failing="nothing")


def test_judge_disagreement_ignores_labels_the_verdict_never_reads():
    first, second = (Labels(claims=[], key_facts=[], is_refusal=True, asks_clarification=a) for a in (True, False))
    assert not judge.disagree("refuse", first, second, [])
    assert judge.disagree("clarify", first, second, [])


def test_a_default_may_not_refuse_what_the_brief_asks_for():
    brief = "Answer questions about wages under the Maritime Labour Convention, 2006."
    docs = [Doc(name="handbook.docx", type="docx", sha256="x")]
    default = [{"id": "Q1", "question": "Refuse Convention questions?", "answer": "Yes. Refuse them.",
                "source": "default"}]
    assert intake.asked_for("Maritime Labour Convention, 2006", brief, docs, default)
    assert intake.asked_for("Wages in handbook.docx", brief, docs, default)
    assert intake.asked_for("General MLC wages (unless referenced)", brief, docs, default)
    assert not intake.asked_for("Library events", brief, docs, default)
    assert not intake.asked_for("wages", "Help with leave. Do not answer about wages.", docs, [])
    assert not intake.asked_for("Convention", brief, docs, [{**default[0], "source": "requester"}])


def test_generator_may_send_sections_as_lists():
    agent = GeneratedAgent(name="a", refusal_message="no", system_prompt={s: ["1. A.", "2. B."] for s in SECTIONS})
    assert agent.system_prompt["role"] == "1. A.\n2. B."


def test_generator_rules_may_not_state_invented_numbers():
    section, invented = generator.drop_invented_numbers(
        "1. Quote the text.\n2. Say seafarers get 102 hours of rest.\n3. Cite the 2006 text.", {2006.0})
    assert section == "1. Quote the text.\n3. Cite the 2006 text." and len(invented) == 1


def test_a_bare_array_reply_is_read_whole():
    assert len(RawCases.model_validate(parse_json('```json\n[{"question": "a"}, {"question": "b"}]\n```')).cases) == 2
    assert parse_json('Sure [C1] says so. {"ok": true}') == {"ok": True}
    assert parse_json('[{"ok": true}]') == {"ok": True}
    assert len(RawCases.model_validate(parse_json('[{"question": "a"}]')).cases) == 1


def test_wilson_interval():
    low, high = report.wilson(8, 11)
    assert 0.43 < low < 0.44 and 0.90 < high < 0.91


def test_sentence_support_marks_quoted_close_and_unsurveyed():
    from forge.checks import sentence_support, split_sentences
    chunk = Chunk(chunk_id="c1", doc="d.pdf", text=SENTENCE)
    assert sentence_support("You may keep a borrowed DVD for 14 days from issue.", [chunk])[0] == "quoted"
    assert sentence_support("Standard card members keep borrowed DVDs 14 days.", [chunk])[0] == "close"
    assert sentence_support("Members who hold a standard card may keep a borrowed DVD for 21 days.", [chunk])[0] == "none"
    assert sentence_support("Most libraries record late returns as a minor breach.", [chunk])[0] == "none"
    assert sentence_support("Yes, 14 days.", [chunk])[0] == "short"
    assert split_sentences("One is here. Two follows.\nThree") == ["One is here.", "Two follows.", "Three"]
    assert split_sentences("Rules: 1. Rest first. 2. Work later.") == ["Rules: 1.", "Rest first.", "Work later."]


def test_ui_marks_unsourced_sentences_and_escapes_model_text():
    from forge.ui import render_turn
    chunk = Chunk(chunk_id="lib#p3#c1", doc="lib.pdf", text=SENTENCE)
    turn = Turn(status="answered", answer="Members who hold a standard card may keep a borrowed DVD for 14 days. "
                "Late returns <script>alert(1)</script> are fined five pounds each day.", retrieved=[chunk])
    column, panel = render_turn("How long?", turn, "meta", None)
    assert "Quoted · lib, p. 3" in column
    assert column.count("Unsurveyed: no source found") == 1 and "Who can answer" in column
    assert "<script>" not in column and "&lt;script&gt;" in column
    assert "<mark>" in panel


def test_doc_check_catches_a_document_changed_after_testing(tmp_path):
    import hashlib
    from forge.views import doc_check
    run, docs = tmp_path / "runs" / "r1", tmp_path / "docs"
    run.mkdir(parents=True)
    docs.mkdir()
    (docs / "policy.txt").write_text("14 days")
    sha = hashlib.sha256(b"14 days").hexdigest()
    d = {"dir": run, "agent": {"docs_dir": "../../docs", "documents": {"policy.txt": sha}}}
    assert doc_check(d)[0] == "same"
    (docs / "policy.txt").write_text("21 days")
    (docs / "extra.txt").write_text("new")
    state, rows = doc_check(d)
    assert state == "changed" and [r[2] for r in rows] == ["changed", "added"]
    (docs / "policy.txt").unlink()
    assert doc_check(d)[1][0][2] == "missing"
    assert doc_check({**d, "agent": {"docs_dir": "../../gone", "documents": {"policy.txt": sha}}})[0] == "absent"


def test_checker_reasons_are_said_in_plain_words():
    from forge.views import plain
    assert plain("check 2: expected to refuse, status was answered") == "It should have refused, but it answered."
    assert plain("check 4: quote not found in c1: 'x'") == "It quoted words that aren't in the passage."
    assert plain("check 8: expected tool csv_lookup was not called") == "It should have used the csv_lookup tool, and didn't."
    assert plain("missing key fact: rest is 10 hours") == "It left out: rest is 10 hours"
    assert plain("something new") == "something new"
