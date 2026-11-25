"""The tool registry. A tool call returns text for the model plus any citable chunks."""

from pathlib import Path

import yaml

from ..schemas import Chunk, ToolCall
from . import calculator, csv_lookup, date, marine_weather

REGISTRY = {t["name"]: t for t in yaml.safe_load((Path(__file__).parent / "registry.yaml").read_text())}


def call(name: str, args: dict, docs: list) -> ToolCall:
    chunks: list[Chunk] = []
    try:
        if name == "csv_lookup":
            result, chunks = csv_lookup.run(docs, **args)
        elif name == "calculator":
            result = calculator.run(**args)
        elif name == "date":
            result = date.run(**args)
        elif name == "marine_weather":
            result = marine_weather.run(**args)
        else:
            raise ValueError(f"unknown tool: {name}")
    except Exception as e:  # arguments come from a small model: any failure goes back to it as text
        return ToolCall(name=name, args=args, result=f"error: {e}", ok=False)
    return ToolCall(name=name, args=args, result=result, ok=True, chunks=chunks)
