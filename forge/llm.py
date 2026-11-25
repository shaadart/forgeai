"""One OpenAI-compatible client: call cache, token budget, prompts, JSON repair."""

import hashlib
import json
import os
import random
import re
import threading
import time
import tomllib
import urllib.error
import urllib.request
from collections import Counter, deque
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
ATTEMPTS = 60  # about ten minutes of overload: free tiers answer "high demand" many times in a row
THOUGHT = re.compile(r"<thought>.*?(?:</thought>|\Z)", re.S)  # reasoning text some models put before the answer
_slots: dict[str, float] = {}  # model -> earliest time of its next request
_slot_lock = threading.Lock()
_sent: dict[str, deque] = {}  # model -> (time, input tokens) of the requests of the last minute
RETRY_IN = re.compile(r"retry in ([\d.]+)s", re.I)


class LLMError(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


def load_env(path: Path = ROOT / ".env") -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and not line.lstrip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def load_config(path: Path | None = None) -> dict:
    return tomllib.loads((path or ROOT / "forge.toml").read_text())


def load_prompt(name: str) -> tuple[dict, dict[str, str]]:
    """Return (front matter, blocks). The unnamed first block is stored under ''."""
    _, front, body = (PROMPTS / f"{name}.md").read_text().split("---\n", 2)
    meta = dict(line.split(": ", 1) for line in front.strip().splitlines())
    parts = re.split(r"\n<!-- block: (\w+) -->\n", body.rstrip("\n"))
    return meta, {"": parts[0], **dict(zip(parts[1::2], parts[2::2]))}


def fill(template: str, values: dict) -> str:
    """Single pass, so braces inside inserted document text are never re-expanded."""

    def value(match):
        v = values[match.group(1)]
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)

    return re.sub(r"\{\{(\w+)\}\}", value, template)


def parse_json(text: str) -> dict:
    body = re.sub(r"^\s*(```(?:json)?)?\s*", "", text)
    start = 0 if body.startswith("[") else body.find("{")  # a bare array only counts if the reply starts with it
    if start < 0:
        raise ValueError("no JSON object in the reply")
    obj, _ = json.JSONDecoder(strict=False).raw_decode(body[start:])
    if isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], dict):
        return obj[0]  # a single object some models wrap in brackets
    return obj


def _wait_tokens(side: dict, size: int) -> tuple | None:
    """Hold a request until it fits under the model's input-tokens-per-minute limit. Returns its window entry."""
    while side.get("tpm"):
        with _slot_lock:
            window, now = _sent.setdefault(side["model"], deque()), time.monotonic()
            while window and now - window[0][0] >= 60:
                window.popleft()
            if not window or sum(n for _, n in window) + size <= side["tpm"]:
                window.append(entry := (now, size))
                return entry
            wait = 60 - (now - window[0][0])
        time.sleep(max(wait, 0.5))


def _refund_tokens(side: dict, entry: tuple | None) -> None:
    """An overloaded server did not process the request; if it counted it anyway, its 429 says how long to wait."""
    with _slot_lock:
        if entry in _sent.get(side["model"], ()):
            _sent[side["model"]].remove(entry)


def _wait_turn(side: dict) -> None:
    """Space requests to a model that has a requests-per-minute limit."""
    if not side.get("rpm"):
        return
    with _slot_lock:
        slot = max(time.monotonic(), _slots.get(side["model"], 0))
        _slots[side["model"]] = slot + 60 / side["rpm"] + 0.5
    time.sleep(max(slot - time.monotonic(), 0))


def http_transport(side: dict, messages: list, temperature: float, max_tokens: int):
    """POST /chat/completions. Returns (text, prompt_tokens, completion_tokens)."""
    key = os.environ.get(side["api_key_env"])
    if not key:
        raise LLMError(f"environment variable {side['api_key_env']} is not set")
    payload = {
        "model": side["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    error = "unknown error"
    attempts = side.get("attempts", ATTEMPTS)
    for attempt in range(attempts):
        request = urllib.request.Request(
            side["base_url"].rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "forgeai"},
        )
        wait = min(2**attempt, 30) * random.uniform(0.8, 1.2)  # jitter keeps the workers apart
        _wait_turn(side)
        reserved = _wait_tokens(side, len(json.dumps(messages)) // 4)
        try:
            with urllib.request.urlopen(request, timeout=side.get("timeout", 300)) as response:
                data = json.load(response)
            text = THOUGHT.sub("", data["choices"][0]["message"]["content"] or "").strip()
            usage = data.get("usage") or {}
            prompt = usage.get("prompt_tokens") or len(json.dumps(messages)) // 4
            completion = usage.get("completion_tokens") or len(text) // 4
            return text, prompt, max(completion, usage.get("total_tokens", 0) - prompt)  # counts hidden reasoning
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            error = f"HTTP {e.code}: {body[:500]}"
            if e.code == 402:  # out of credit is a spent budget: stop and still write the report
                raise BudgetExceeded(f"the provider reports no credit left (HTTP 402) for {side['model']}") from e
            if e.code == 400 and "response_format" in payload:
                del payload["response_format"]  # provider without JSON mode
                continue
            if e.code not in (408, 409, 429) and e.code < 500:
                break
            if e.code == 503:
                _refund_tokens(side, reserved)
                wait = min(wait, 8 * random.uniform(0.8, 1.2))
            retry_after = e.headers.get("Retry-After", "")
            if retry_after.isdigit():
                wait = min(int(retry_after), 60)
            elif delay := RETRY_IN.search(body):
                wait = min(float(delay.group(1)), 90) + random.uniform(1, 5)
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError, json.JSONDecodeError) as e:
            error = f"{type(e).__name__}: {e}"
            if isinstance(getattr(e, "reason", None), ConnectionRefusedError) and attempt >= 3:
                break  # nothing is listening there; ten minutes of retries would not help
        if attempt < attempts - 1:
            time.sleep(wait)
    raise LLMError(f"{side['model']}: {error}")


class LLM:
    def __init__(self, config: dict, log_path: Path | None = None, budget: int | None = None,
                 replay: bool = False, transport=http_transport):
        self.config = config
        limits = config.get("limits", {})
        self.budget = budget or limits.get("budget_tokens", 3_000_000)
        self.max_output = limits.get("max_output_tokens", 3000)
        self.workers = limits.get("workers", 6)
        self.log_path = log_path
        self.replay = replay
        self.transport = transport
        self.lock = threading.Lock()
        self.cache: dict[str, dict] = {}
        self.contract_failures: Counter = Counter()
        if log_path and log_path.is_file():
            for line in log_path.read_text().splitlines():
                try:
                    entry = json.loads(line)
                    self.cache[entry["key"]] = entry
                except (json.JSONDecodeError, KeyError):
                    continue  # a crash can leave a torn last line

    @property
    def tokens(self) -> int:
        return sum(e["prompt_tokens"] + e["completion_tokens"] for e in list(self.cache.values()))

    def usage(self) -> dict:
        entries = list(self.cache.values())
        return {"calls": len(entries), "tokens": self.tokens, "limit": self.budget,
                "seconds": round(sum(e["seconds"] for e in entries), 1)}

    def chat(self, side: str, messages: list, temperature: float = 0.0, stage: str = "", sample: int = 0) -> str:
        """`sample` separates deliberate repeat calls that would otherwise share a cache entry."""
        cfg = self.config[side]
        max_output = cfg.get("max_output_tokens", self.max_output)
        key = hashlib.sha256(
            json.dumps([cfg["model"], messages, temperature, max_output, sample], sort_keys=True).encode()
        ).hexdigest()
        if key in self.cache:
            return self.cache[key]["response"]
        if self.replay:
            raise LLMError(f"replay: no cached call for stage '{stage}'")
        if self.tokens >= self.budget:
            raise BudgetExceeded(f"token budget of {self.budget} spent")
        started = time.monotonic()
        text, prompt_tokens, completion_tokens = self.transport(cfg, messages, temperature, max_output)
        entry = {"key": key, "stage": stage, "side": side, "model": cfg["model"], "temperature": temperature,
                 "sample": sample, "messages": messages, "response": text, "prompt_tokens": prompt_tokens,
                 "completion_tokens": completion_tokens, "seconds": round(time.monotonic() - started, 2)}
        with self.lock:
            self.cache[key] = entry
            if self.log_path:
                with self.log_path.open("a") as log:
                    log.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return text

    def parsed(self, side: str, messages: list, temperature: float, schema, stage: str, sample: int = 0):
        """Call, validate, repair once. Returns None after a second bad reply."""
        for _ in range(2):
            text = self.chat(side, messages, temperature, stage, sample)
            try:
                return schema.model_validate(parse_json(text))
            except (ValueError, ValidationError) as e:
                repair = load_prompt("00_repair")[1][""]
                messages = messages + [
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": fill(repair, {"validation_error": str(e)[:600]})},
                ]
        with self.lock:
            self.contract_failures[stage] += 1
        return None

    def ask(self, prompt: str, values: dict, schema, stage: str, sample: int = 0):
        meta, blocks = load_prompt(prompt)
        messages = [{"role": "user", "content": fill(blocks[""], values)}]
        return self.parsed(meta["side"], messages, float(meta["temperature"]), schema, stage, sample)
