"""Real generator, real model, 3 out of 3. Skipped without an API key; costs about 12 calls."""

import os

import pytest

from forge import generator, intake, inventory
from forge.llm import LLM, load_config, load_env

load_env()
CONFIG = load_config()
pytestmark = pytest.mark.skipif(not os.environ.get(CONFIG["builder"]["api_key_env"]), reason="no model API key")

SPARES_CSV = "part_no,description,price,currency,lead_time_days\nPMP-001,Pump seal,42.00,USD,9\n"
CASES = {
    "mlc": ("Answer seafarers' questions about rest hours, leave, wages and repatriation.", set()),
    "weather_word_trap": ("Crew say rough weather is cutting into their rest hours. What are the rest rules?", set()),
    "spares": ("Help purchasers find pump spares in the catalogue, work out order totals, and say whether an order "
               "can arrive before a given port call date, counting from today.", {"csv_lookup", "calculator", "date"}),
    "voyage_weather": ("Brief the master on the live sea state forecast along tomorrow's route.", {"marine_weather"}),
}


@pytest.mark.parametrize("name", CASES)
def test_attaches_only_needed_tools(name, tmp_path):
    brief, expected = CASES[name]
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    if name == "spares":
        (docs_dir / "catalogue.csv").write_text(SPARES_CSV)
    else:
        (docs_dir / "rules.md").write_text("# Rest\nMinimum rest is 10 hours in any 24 hour period.\n")
    docs = inventory.scan(docs_dir)
    for sample in range(3):
        llm = LLM(CONFIG)
        # `sample` bypasses the cache so that three runs are three real answers
        original = llm.chat
        llm.chat = lambda side, messages, temperature=0.0, stage="", _=0: original(
            side, messages, temperature, stage, sample)
        requirements = intake.requirements(llm, brief, docs, [])
        agent, _ = generator.generate(llm, requirements, docs, docs_dir, tmp_path)
        tools = {t.name for t in agent.tools}
        if name == "voyage_weather":
            assert "marine_weather" in tools
        else:
            assert tools == expected
