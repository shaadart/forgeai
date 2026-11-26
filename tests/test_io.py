"""The edges that touch the outside: the HTTP client and the document loaders."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pytest
from docx import Document
from pypdf import PdfWriter

from forge import canaries, cli, groundability, intake, inventory, judge
from forge import llm as llm_module
from forge.index import Index
from forge.llm import LLM, BudgetExceeded, LLMError
from forge.schemas import Quote, Topic


def _pdf(text: str) -> bytes:
    """The smallest one-page PDF with a text layer."""
    stream = f"BT /F1 12 Tf 20 700 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    body, offsets = b"%PDF-1.4\n", []
    for n, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body += b"%d 0 obj\n%s\nendobj\n" % (n, obj)
    xref = b"xref\n0 6\n0000000000 65535 f \n" + b"".join(b"%010d 00000 n \n" % o for o in offsets)
    return body + xref + b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % len(body)


def test_loaders_read_pdf_docx_and_flag_what_they_cannot_read(tmp_path):
    (tmp_path / "terms.pdf").write_bytes(_pdf("Section 2 Payment is due within thirty days of the invoice date."))
    writer = PdfWriter()
    writer.add_blank_page(612, 792)
    writer.write(tmp_path / "scan.pdf")
    document = Document()
    document.add_heading("Leave", 1)
    document.add_paragraph("Staff get annual leave.")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text, table.rows[0].cells[1].text = "Grade A", "25 days"
    document.save(tmp_path / "hr.docx")
    (tmp_path / "broken.pdf").write_bytes(b"not a pdf")
    (tmp_path / "t.csv").write_text('part,note\nA-1,"two\nlines"\n')

    docs = {d.name: d for d in inventory.scan(tmp_path)}
    assert "thirty days" in docs["terms.pdf"].segments[0].text
    assert not docs["scan.pdf"].read and "scanned" in docs["scan.pdf"].note
    assert not docs["broken.pdf"].read
    assert "Grade A | 25 days" in docs["hr.docx"].segments[0].text and docs["hr.docx"].headings == ["Leave"]
    assert docs["t.csv"].records == [{"part": "A-1", "note": "two\nlines"}]


def test_http_client_drops_json_mode_when_refused_and_caches(tmp_path, monkeypatch):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(payload)
            if self.path.startswith(("/denied", "/broke")):
                self.send_response(401 if self.path.startswith("/denied") else 402)
                self.end_headers()
                return
            code = 400 if "response_format" in payload else 200
            self.send_response(code)
            self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"content": '{"ok": true}'}}],
                                         "usage": {"prompt_tokens": 3, "completion_tokens": 2}}).encode())

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("TEST_KEY", "k")
    url = f"http://127.0.0.1:{server.server_port}"
    side = {"base_url": url, "model": "m", "api_key_env": "TEST_KEY"}
    llm = LLM({"builder": side}, tmp_path / "calls.jsonl")
    message = [{"role": "user", "content": "hi"}]
    assert llm.chat("builder", message) == '{"ok": true}'
    assert llm.chat("builder", message) == '{"ok": true}' and len(seen) == 2 and llm.tokens == 5
    assert '"k"' not in (tmp_path / "calls.jsonl").read_text()
    with pytest.raises(BudgetExceeded):
        LLM({"builder": {**side, "base_url": url + "/broke"}}).chat("builder", message)
    with pytest.raises(LLMError, match="401"):
        LLM({"builder": {**side, "base_url": url + "/denied"}}).chat("builder", message)
    server.shutdown()


def test_missing_brief_is_a_message_not_a_traceback(tmp_path):
    with pytest.raises(SystemExit, match="error: .*nope.txt"):
        cli.main(["build", "--brief", str(tmp_path / "nope.txt"), "--docs", str(tmp_path)])


def test_bracketed_citation_ids_are_cleaned():
    assert Quote(chunk_id="[a#p1#c1]", quote="x").chunk_id == "a#p1#c1"


def test_requests_wait_for_the_token_limit(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(llm_module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    side = {"model": "tpm-test", "tpm": 100}
    for size in (80, 20):
        llm_module._wait_tokens(side, size)
    assert clock[0] == 1000.0  # both fit in one minute
    llm_module._wait_tokens(side, 50)
    assert clock[0] == 1060.0
    llm_module._refund_tokens(side, llm_module._wait_tokens(side, 50))  # an overloaded reply costs nothing
    llm_module._wait_tokens(side, 50)
    assert clock[0] == 1060.0


def test_reasoning_text_is_removed_before_parsing(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            content = '<thought>maybe {"ok": false}</thought>{"ok": true}'
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"content": content}}], "usage": {
                "prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 50}}).encode())

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("TEST_KEY", "k")
    llm = LLM({"builder": {"base_url": f"http://127.0.0.1:{server.server_port}", "model": "t", "api_key_env": "TEST_KEY"}})
    assert llm.chat("builder", [{"role": "user", "content": "hi"}]) == '{"ok": true}' and llm.tokens == 50
    server.shutdown()


def test_invented_part_numbers_are_replaced_and_rows_cover_every_supplier(tmp_path):
    rows = "".join(f"N-BP2-{n:02d},seal,Nordsee\n" for n in range(12))
    (tmp_path / "c.csv").write_text("part_no,description,supplier\n" + rows + "G-BP2-01,gasket,Gulfstream\n")
    docs = inventory.scan(tmp_path)
    topic = Topic(id="T1", topic="Finding spares", example_question="Who supplies part P12345 and G-BP2-01?")
    intake._real_examples([topic], "find spares", docs)
    assert topic.example_question == "What are the description, supplier for part_no N-BP2-00?"
    assert len(inventory.summary(docs)[0]["sample_rows"]) == 3
    index = Index(docs, lambda texts: np.ones((len(texts), 2), np.float32) / np.sqrt(2))
    nearest = index.chunks(groundability.WIDE)[:8]
    assert any("Gulfstream" in c.text for c in groundability._other_values(index, nearest))


def test_the_row_named_by_a_part_number_ranks_first(tmp_path):
    rows = "".join(f"N-BP2-{n:02d},mechanical seal\n" for n in range(30))
    (tmp_path / "c.csv").write_text("part_no,description\n" + rows)
    index = Index(inventory.scan(tmp_path), lambda texts: np.ones((len(texts), 2), np.float32) / np.sqrt(2))
    assert "N-BP2-23;" in index.search("minimum order quantity for mechanical seal N-BP2-23?")[0].text


def test_placeholder_numbers_are_dropped_and_the_swap_targets_a_stated_fact(tmp_path):
    (tmp_path / "c.csv").write_text("part_no,description\nN-BP2-01,seal\n")
    topic = Topic(id="T1", topic="Pump spares", example_question="What spares fit the 5678 pump?")
    intake._real_examples([topic], "find spares", inventory.scan(tmp_path))
    assert topic.example_question == "What are the description for part_no N-BP2-01?"
    swapped = canaries._swap_digit("See paragraph 6. Luggage of 30 kg.", "Luggage of 30 kg.")
    assert "paragraph 6" in swapped and "40 kg" in swapped


def test_judge_accepts_two_cited_items_and_skips_claims_about_the_reply():
    reply = {"claims": [{"claim": "Orders are in the supplier currency.", "verdict": "supported", "evidence_id": "E1, E2"},
                        {"claim": "Payment is due in 30 days.", "verdict": "supported", "evidence_id": ["E2", "E1"]},
                        {"claim": "The assistant cannot help with wages.", "verdict": "unsupported"},
                        {"claim": "A seafarer cannot be dismissed.", "verdict": "supported", "evidence_id": "E9"},
                        {"claim": "You should ask your manager or the responsible department.", "verdict": "unsupported"},
                        {"claim": "The information could not be found in the documents.", "verdict": "unsupported"},
                        {"claim": "Ask your manager, who approves 900 EUR.", "verdict": "unsupported"}],
             "key_facts": [], "is_refusal": True, "asks_clarification": False}

    class Stub:
        def ask(self, prompt, values, schema, stage, sample=0):
            return schema.model_validate(reply)

    claims = judge.label(Stub(), "q", "a", ["one", "two"], []).claims
    assert [(c.verdict, c.evidence_id) for c in claims] == [
        ("supported", "E1"), ("supported", "E2"), ("unsupported", None), ("unsupported", None)]


def test_the_checker_is_told_about_the_calculator_only_for_arithmetic_topics():
    seen = []

    class Stub:
        def ask(self, prompt, values, schema, stage, sample=0):
            seen.append("note" in values["topic_json"])

    for capabilities in (["retrieval"], ["retrieval", "arithmetic"]):
        groundability._ask(Stub(), Topic(id="T1", topic="Totals", example_question="Total?", capabilities=capabilities), [])
    assert seen == [False, True]


def test_code_overrules_a_denied_table_row_only_when_the_question_names_its_item(tmp_path):
    (tmp_path / "c.csv").write_text('part_no,description,unit_price\nN-1,"Impeller, bronze",42.00\n')
    index = Index(inventory.scan(tmp_path), lambda texts: np.ones((len(texts), 2), np.float32) / np.sqrt(2))
    chunks = index.chunks()

    def named(question, capabilities):
        topic = Topic(id="T1", topic="Totals", example_question=question, capabilities=capabilities)
        return groundability._named_row(index, topic, chunks)

    assert named("Total cost of 3 impellers?", ["arithmetic"])
    assert not named("Total cost of 3 impellers?", ["retrieval"])
    assert not named("Can it arrive before the port call?", ["lookup_rows"])


def test_arithmetic_needs_a_brief_that_asks_for_sums():
    assert intake.SUMS.search("find spares and work out order totals")
    assert not intake.SUMS.search("Answer questions about rest hours, leave, wages and repatriation.")
