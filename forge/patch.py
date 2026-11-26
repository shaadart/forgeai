"""Code checks on a proposed patch: whitelist, bounds, size, leakage, repeats."""

from .checks import ngrams
from .schemas import BOUNDS, AgentDef, Patch

MAX_OPS = 3
MAX_ADDED_WORDS = 60
LEAK_GRAM = 4


class PatchRejected(ValueError):
    pass


def signature(patch: Patch) -> list[dict]:
    return [op.model_dump(exclude_none=True) for op in patch.ops]


def apply(agent: AgentDef, patch: Patch, allowed: list[str], train_texts: list[str], history: list[dict],
          required_refusals: list[str] = ()) -> tuple[AgentDef, list[dict]]:
    """Return (new agent, changes with from/to), or raise PatchRejected."""
    if not patch.ops:
        raise PatchRejected("empty patch")
    if len(patch.ops) > MAX_OPS:
        raise PatchRejected(f"more than {MAX_OPS} operations")
    if any(h["ops"] == signature(patch) and not h["accepted"] for h in history):
        raise PatchRejected("repeats a patch that was already rejected")
    protected = set().union(*(ngrams(t, LEAK_GRAM) for t in train_texts))
    existing = set().union(*(ngrams(t, LEAK_GRAM) for t in agent.system_prompt.values()))
    data = agent.model_dump()
    changes, added_words = [], 0
    for op in patch.ops:
        if op.path not in allowed:
            raise PatchRejected(f"path not allowed: {op.path}")
        _, area, name = op.path.split("/")
        if area == "retrieval":
            value, (low, high) = op.value, BOUNDS[name]
            if op.op != "set" or type(value) not in (int, float):
                raise PatchRejected(f"{op.path} takes a set operation with a number")
            if isinstance(low, int) and value != int(value):
                raise PatchRejected(f"{op.path} must be a whole number")
            if not low <= value <= high:
                raise PatchRejected(f"{op.path}={value} is outside {low}..{high}")
            value = int(value) if isinstance(low, int) else float(value)
            if data["retrieval"][name] == value:
                raise PatchRejected(f"{op.path} is already {value}")
            changes.append({"op": "set", "path": op.path, "from": data["retrieval"][name], "to": value})
            data["retrieval"][name] = value
            continue
        section = data["system_prompt"][name]
        if op.op == "append_rule" and isinstance(op.value, str) and op.value.strip():
            old, new = "", op.value.strip()
            data["system_prompt"][name] = f"{section}\n{len(section.splitlines()) + 1}. {new}"
        elif op.op == "replace_sentence" and op.old and op.new is not None:
            old, new = op.old, op.new
            if old not in section:
                raise PatchRejected(f"sentence to replace is not in {op.path}")
            data["system_prompt"][name] = section.replace(old, new, 1)
        else:
            raise PatchRejected(f"invalid operation on {op.path}")
        if (ngrams(new, LEAK_GRAM) - existing) & protected:
            raise PatchRejected("leakage: the new text copies a train question or fact")
        added_words += max(len(new.split()) - len(old.split()), 0)
        changes.append({"op": op.op, "path": op.path, "from": old, "to": new})
    if added_words > MAX_ADDED_WORDS:
        raise PatchRejected(f"adds {added_words} words; the limit is {MAX_ADDED_WORDS}")
    policy = data["system_prompt"]["refusal_policy"].lower()
    dropped = [t for t in required_refusals if t.lower() not in policy]
    if dropped:
        raise PatchRejected(f"removes a must-refuse topic from the refusal policy: {dropped[0]}")
    data["version"] = agent.version + 1
    return AgentDef.model_validate(data), changes
