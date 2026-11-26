"""The whole factory, offline, with a scripted model."""

import json

from fakes import BRIEF, FEES, POLICY, embed, make_transport
from forge import inventory, pipeline
from forge.index import Index
from forge.llm import LLM, load_config
from forge.runtime import load_agent, run_turn, stale_documents


def _docs(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "loan_policy.md").write_text(POLICY)
    (folder / "fees.csv").write_text(FEES)
    (folder / "photo.png").write_bytes(b"not a document")
    return folder


def test_end_to_end_then_replay(tmp_path):
    folder, run_dir = _docs(tmp_path), tmp_path / "run"
    run_dir.mkdir()
    llm = LLM(load_config(), run_dir / "llm_calls.jsonl", transport=make_transport())
    assert pipeline.build(run_dir, BRIEF, folder, llm, embed) == pipeline.OK

    for name in ("requirements.json", "requirements.final.json", "groundability.json", "agent.v0.yaml",
                 "agent.final.yaml", "evalset.jsonl", "evalset.rejected.jsonl", "split.json", "canaries.json",
                 "iterations.jsonl", "scorecard.json", "report.md"):
        assert (run_dir / name).is_file(), name
    card = json.loads((run_dir / "scorecard.json").read_text())
    agent = load_agent(run_dir / "agent.final.yaml")
    assert agent.tools == []  # the weather tool had no valid link, so code dropped it
    assert "Fine disputes" in agent.system_prompt["refusal_policy"]
    assert len(json.loads((run_dir / "questions.json").read_text())["asked"]) == 1  # bad trigger dropped
    assert card["assumptions"], "unattended defaults must be recorded"
    assert any("photo.png" in d for d in card["documents_not_read"])
    assert card["sealed"]["final"]["total"] > 0 and card["train"]["final"]["total"] > 0
    assert card["judge"]["health"] == "ok", card["judge"]["canaries"]
    assert card["loop"]["accepted"] == 1 and agent.version == 1
    assert card["train"]["final"]["passed"] > card["train"]["v0"]["passed"]
    assert all(f["still_open_because"] for f in card["failures"])
    report_text = (run_dir / "report.md").read_text()
    assert all(f["id"] in report_text for f in card["failures"])

    ids = {json.loads(line)["id"][0] for line in (run_dir / "evalset.jsonl").read_text().splitlines()}
    assert ids == {"T", "S"}

    docs = inventory.scan(folder)
    assert stale_documents(agent, docs) == []
    assert run_turn(llm, agent, Index(docs, embed), "How long is a DVD loan?").status == "answered"
    (folder / "fees.csv").write_text(FEES + "CD,1.00,GBP\n")
    assert stale_documents(agent, inventory.scan(folder)) == ["fees.csv"]
    (folder / "fees.csv").write_text(FEES)

    # every call of the run is in the log, so a replay needs no model at all
    replay = LLM(load_config(), run_dir / "llm_calls.jsonl", replay=True, transport=None)
    assert pipeline.build(run_dir, BRIEF, folder, replay, embed) == pipeline.OK


def test_spent_budget_still_reports(tmp_path):
    folder, run_dir = _docs(tmp_path), tmp_path / "run"
    llm = LLM(load_config(), budget=700, transport=make_transport())
    assert pipeline.build(run_dir, BRIEF, folder, llm, embed) == pipeline.BUDGET_SPENT
    assert "stopped early" in (run_dir / "report.md").read_text()


def test_empty_folder_stops_before_any_model_call(tmp_path):
    folder, run_dir = tmp_path / "docs", tmp_path / "run"
    folder.mkdir()
    llm = LLM(load_config(), transport=None)  # any call would fail
    assert pipeline.build(run_dir, BRIEF, folder, llm, embed) == pipeline.NOT_GROUNDABLE
    assert "folder is empty" in (run_dir / "report.md").read_text()


def test_ungroundable_brief_stops_with_a_report(tmp_path):
    folder, run_dir = _docs(tmp_path), tmp_path / "run"
    base = make_transport()

    def transport(side, messages, *rest):
        if messages[0]["content"].startswith("You check whether"):
            return json.dumps({"verdict": "unsupported", "missing": "nothing there"}), 1, 1
        return base(side, messages, *rest)

    llm = LLM(load_config(), transport=transport)
    assert pipeline.build(run_dir, BRIEF, folder, llm, embed) == pipeline.NOT_GROUNDABLE
    assert "not groundable" in (run_dir / "report.md").read_text()
    assert not (run_dir / "agent.v0.yaml").exists()
