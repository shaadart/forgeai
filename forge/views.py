"""What the web UI shows: reads a run folder and renders it as HTML. Every model or document string is escaped."""

import hashlib
import html
import json
import re
import tomllib
from collections import Counter
from functools import lru_cache
from pathlib import Path

import yaml

from . import jobs, report
from .checks import NUMBER, context_chunks, sentence_support, split_sentences, strip_citations
from .schemas import DEFAULT_REFERRAL, Result, Turn

E = html.escape
CANARIES = {"gold": "a correct answer", "number_swap": "a swapped number", "padded": "a padded answer",
            "planted_claim": "an added false claim", "shuffled": "shuffled evidence",
            "correct_refusal": "a correct refusal"}
LIMIT = ("A colour mark shows where the words came from. A marked sentence can still be wrong. "
         "A sentence built from two passages can show as unsurveyed.")
PROBLEM = {  # the factory's failure categories, in plain words
    "hallucination": "Made something up",
    "retrieval_miss": "Didn't find the right passage",
    "prompt_defect": "Didn't follow its instructions",
    "wrong_refusal": "Refused a question it could answer",
    "judge_uncertain": "The grader couldn't decide",
    "eval_defect": "The test question was faulty",
}
NEXT_STEP = {  # chosen by code from the failure category. A starting point, checked by nobody
    "judge_uncertain": "Read the answer yourself and decide.",
    "hallucination": "Read the agent's refusal and grounding rules against this question, then run again.",
    "retrieval_miss": "Check which passages came back. Try a higher top_k or another chunk size.",
    "prompt_defect": "Compare the answer with its passage, then edit the matching prompt section.",
    "wrong_refusal": "Check whether this topic belongs on the refusal list.",
    "eval_defect": "Fix or drop this test question.",
}
DID = {"answer": "answered", "refuse": "refused", "clarify": "asked a question back", "answered": "answered",
       "refused": "refused", "needs_clarification": "asked a question back"}
SHOULD = {"answer": "answered", "refuse": "refused", "clarify": "asked a question back"}


def plain(reason: str) -> str:
    """One of the checker's reasons in words a child can read. Unknown wording passes through unchanged."""
    if m := re.match(r"check 2: expected to (\w+), status was (\w+)", reason):
        return f"It should have {SHOULD.get(m[1], m[1])}, but it {DID.get(m[2], m[2])}."
    for start, said in (
            ("check 1", "Its reply wasn't in the required format."),
            ("check 3", "It pointed to a passage it was never given."),
            ("check 4", "It quoted words that aren't in the passage."),
            ("the two judge passes disagree", "The grader read it twice and gave two different answers."),
            ("a judge canary failed", "The grader failed its own test, so this verdict can't be trusted."),
            ("the judge returned no usable labels", "The grader gave no usable answer."),
            ("a number is not in the context", "It used a number the documents don't have, and the grader let it pass."),
            ("the judge does not read the reply as a refusal", "The grader didn't read the reply as a refusal.")):
        if reason.startswith(start):
            return said
    if m := re.match(r"check 8: expected tool (\S+) was not called", reason):
        return f"It should have used the {m[1]} tool, and didn't."
    if m := re.match(r"check 8: called unattached tool (\S+)", reason):
        return f"It tried to use {m[1]}, a tool it doesn't have."
    for start, said in (("unsupported claim: ", "It said something the documents don't back up: "),
                        ("contradicted claim: ", "It said something the documents contradict: "),
                        ("missing key fact: ", "It left out: ")):
        if reason.startswith(start):
            return said + reason[len(start):]
    return reason


def step(number: int, title: str) -> str:
    return f'<p class="stephead"><b aria-hidden="true">{number}</b>{title}</p>'


def mark(state: str) -> str:
    """The chart mark for a verdict: solid square, danger mark, hatched square. Always printed beside its word."""
    return f'<span class="oc oc-{state}" aria-hidden="true"></span>'


def chip(inner: str) -> str:
    return f'<span class="chip">{inner}</span>'


def outcome(state: str) -> str:
    return f'<span class="out st-{state}">{mark(state)}{state.capitalize()}</span>'


def say(text: str) -> str:
    return f'<div class="fg box"><p role="status">{E(text)}</p></div>'


# --- reading a run folder ---


def _json(path: Path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):  # missing, or half written by a running build
        return default


def _lines(path: Path) -> list:
    rows = []
    for line in path.read_text(errors="replace").splitlines() if path.is_file() else []:
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def _n(count: int, word: str) -> str:
    return f"{count} {word}{'s' * (count != 1)}"


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + " …"


def list_runs(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "run.json").is_file() or (p / jobs.PID).is_file())


def _agent(run_dir: Path) -> dict | None:
    try:
        return yaml.safe_load((run_dir / "agent.final.yaml").read_text())
    except (OSError, yaml.YAMLError):
        return None


def run_choices(root: Path) -> list[tuple[str, str]]:
    """(agent name, run id) for the rail. Runs that share a name show their id too."""
    names = {r: (_agent(root / r) or {}).get("name") or r for r in list_runs(root)}
    seen = Counter(names.values())
    return [(f"{name} · {r}" if seen[name] > 1 else name, r) for r, name in names.items()]


def load(run_dir: Path) -> dict:
    results, split_of = {}, {}
    for split in ("sealed", "train"):
        for case_id, raw in (_json(run_dir / f"results.{split}_final.json") or {}).items():
            results[case_id], split_of[case_id] = Result.model_validate(raw), split
    return {"dir": run_dir, "run": _json(run_dir / "run.json", {}), "card": _json(run_dir / "scorecard.json"),
            "req": _json(run_dir / "requirements.final.json"), "results": results, "split": split_of,
            "agent": _agent(run_dir), "cases": {c["id"]: c for c in _lines(run_dir / "evalset.jsonl")},
            "log": _lines(run_dir / "iterations.jsonl"), "inventory": _json(run_dir / "inventory.json", [])}


def models(d: dict) -> dict:
    """Builder and examiner model names from the run's config file, when it is on disk."""
    path = Path(d["run"].get("config") or "")
    if not path.is_file():
        return {}
    config = tomllib.loads(path.read_text())
    return {side: config.get(side, {}).get("model", "?") for side in ("builder", "examiner")}


def synthetic(d: dict) -> bool:
    texts = [" ".join(doc.get("headings") or []) for doc in d["inventory"]]
    texts += [c.text for r in d["results"].values() for c in r.turn.retrieved]
    return any("synthetic" in t.lower() for t in texts)


def doc_check(d: dict) -> tuple[str, list[tuple[str, str, str]]]:
    """Do the documents on disk still match the ones the agent was tested on? Hashes decide.

    Returns ("same" | "changed" | "absent" | "none", [(file, tested sha256, status)]).
    """
    tested = (d["agent"] or {}).get("documents") or {}
    if not tested:
        return "none", []
    folder = (d["dir"].resolve() / d["agent"].get("docs_dir", "")).resolve()
    if not folder.is_dir():
        return "absent", [(name, sha, "not here") for name, sha in tested.items()]
    now = {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in folder.rglob("*") if p.is_file()}
    rows = [(name, sha, "unchanged" if now.get(name) == sha else "changed" if name in now else "missing")
            for name, sha in tested.items()]
    rows += [(name, sha, "added") for name, sha in now.items() if name not in tested]
    return ("same" if all(r[2] == "unchanged" for r in rows) else "changed"), rows


def question_of(d: dict, case_id: str) -> str:
    return d["cases"].get(case_id, {}).get("question", "?")


def case_order(d: dict) -> list[str]:
    return sorted(d["results"], key=lambda i: (d["split"][i] != "sealed", i))


def support_of(turn: Turn) -> list[tuple]:
    """(sentence, support, chunk, matched words) for each sentence. A refusal makes no claim, so it has none."""
    if turn.status == "refused":
        return []
    chunks = context_chunks(turn)
    return [(s, *sentence_support(s, chunks)) for s in split_sentences(strip_citations(turn).replace("**", ""))]


@lru_cache(maxsize=1024)
def _support_counts(turn_json: str) -> tuple:
    found = Counter(m[1] for m in support_of(Turn.model_validate_json(turn_json)))
    return found["quoted"], found["close"], found["none"]


def support_counts(result: Result) -> tuple[int, int, int]:
    """(quoted, close, unsurveyed) sentences in one recorded answer."""
    return _support_counts(result.turn.model_dump_json())


# --- the head of an agent's page ---


def hero(d: dict, live_model: str | None) -> str:
    name = (d["agent"] or {}).get("name") or "Agent not built yet"
    req = d["req"] or {}
    scope = req.get("scope", "The requirements aren't written yet.")
    state = {"finished": "Run finished", "running": "Run in progress", "stopped": "Run stopped",
             "not_groundable": "Not built", "outside": "Run not finished"}[jobs.state(d["dir"])]
    facts = [f"Live: your question goes to {live_model}. I don't store the chat." if live_model else
             "Replay: no model is connected, so you can read the answers it gave in the test."]
    if audience := req.get("audience"):
        facts.insert(0, f"Made for {audience if audience[:2].isupper() else audience[0].lower() + audience[1:]}.")
    if synthetic(d):
        facts.append("Some documents are made-up demo content.")
    if state != "Run finished":
        facts.append(f"{state}.")
    check, rows = doc_check(d)
    changed = ", ".join(r[0] for r in rows if r[2] != "unchanged")
    integrity = {
        "same": ("passed", f"The {_n(len(rows), 'document')} haven't changed since this agent was tested."),
        "changed": ("failed", f"Documents changed since the test: {changed}. The scores no longer apply."),
        "absent": ("unknown", "The documents aren't on this machine, so I can't check them."),
    }.get(check)
    line = f'<p class="integrity st-{integrity[0]}">{mark(integrity[0])}{E(integrity[1])}</p>' if integrity else ""
    return (f'<div class="fg hero"><h2>{E(name)}</h2><p class="scope">{E(scope)}</p>'
            f'<p class="facts">{E(" ".join(facts))}</p>{line}</div>')


def _missed(card: dict) -> list[str]:
    return [CANARIES.get(c["name"], c["name"]) for c in card["judge"]["canaries"] if not c["ok"]]


def _rate(card: dict) -> str:
    sealed = card["sealed"]["final"]
    decided = sealed["passed"] + sealed["failed"]
    if _missed(card):
        return "No usable score: the grader failed its own test, so only verdicts decided by code remain."
    if not decided:
        return "No question was decided, so there's no score."
    return (f"{report.pct(sealed['rate'])} of the {decided} decided questions passed. With so few, the real rate could "
            f"be anywhere from {report.pct(sealed['ci'][0])} to {report.pct(sealed['ci'][1])} (95% interval).")


def _verdicts(tally: dict) -> str:
    return "".join(f'<span class="st-{s}">{mark(s)}<b>{tally[s]}</b> {s}</span>' for s in ("passed", "failed", "unknown"))


def _bar(tally: dict) -> str:
    """One bar, cut in proportion: a child can see how much passed. The numbers sit beside it in words."""
    parts = "".join(f'<i class="seg-{s}" style="flex-grow:{tally[s]}"></i>'
                    for s in ("passed", "failed", "unknown") if tally[s])
    return f'<div class="bar" aria-hidden="true">{parts}</div>'


def trust(d: dict) -> str:
    """The one thing to know before asking: can this agent be trusted, and how far."""
    card = d["card"]
    if card is None:
        return ('<div class="fg trust"><h3>Not tested yet</h3><p>Open How it was built to see how far this run got.</p>'
                '<button type="button" data-goto="log">See how it was built</button></div>')
    sealed = card["sealed"]["final"]
    counts = [support_counts(r) for r in d["results"].values()]
    sentences, loose = sum(map(sum, counts)), sum(c[2] for c in counts)
    grader = ('<p class="warn-line">' + mark("failed") + "The grader failed its own test, so don't trust this score yet."
              "</p>" if _missed(card) else "")
    score = (f'{_bar(sealed)}<p class="verdicts">{_verdicts(sealed)}</p>' if sealed else "<p>The hidden test never ran.</p>")
    return (f'<div class="fg trust"><div class="trust-words"><h3>How far can you trust it?</h3>'
            f'<p>On questions kept hidden while it was being fixed:</p></div><div class="trust-score">{score}</div>'
            f'<p class="trust-note">{loose} of {sentences} sentences in its test answers have no source.</p>{grader}'
            '<button type="button" data-goto="certificate">Open report card</button></div>')


# --- ask: the list of recorded questions, one answer, its sources ---


def case_list(d: dict, selected: str | None = None, stamp: int = 0) -> str:
    """Search and filters run in the browser (ui.LIST_JS); a row click asks Python for that answer."""
    if not d["results"]:
        return f'<div class="fg box">{step(1, "Pick a question")}<p class="muted">This run has no test answers yet.</p></div>'
    loose = {i: support_counts(r)[2] for i, r in d["results"].items()}
    counts = Counter(r.state for r in d["results"].values())
    filters = "".join(
        f'<button type="button" data-filter="{key}" aria-pressed="{str(key == "all").lower()}">{label} '
        f"<span>{count}</span></button>"
        for key, label, count in [("all", "All", len(d["results"])),
                                  *((s, s.capitalize(), counts[s]) for s in ("failed", "unknown", "passed")),
                                  ("unsurveyed", "No source", sum(n > 0 for n in loose.values()))])
    rows = []
    for i in case_order(d):
        state, question = d["results"][i].state, question_of(d, i)
        flag = f' · <span class="loose">{loose[i]} with no source</span>' if loose[i] else ""
        rows.append(f'<li data-tags="{state}{" unsurveyed" if loose[i] else ""}" data-text="{E((i + " " + question).lower())}">'
                    f'<button type="button" data-case="{E(i)}" aria-pressed="{str(i == selected).lower()}">'
                    f'<span class="what"><span class="q2">{E(question)}</span><span class="sub st-{state}">{mark(state)}'
                    f'{state.capitalize()} · {E(i)}{flag}</span></span></button></li>')
    return (f'<div class="fg box questions" data-stamp="{stamp}">{step(1, "Pick a test question")}'
            '<input type="search" data-search placeholder="Search questions" aria-label="Search recorded questions">'
            f'<div class="filters" role="group" aria-label="Filter questions">{filters}</div>'
            f'<ul class="rows">{"".join(rows)}</ul><p class="muted" data-empty hidden>No question matches. '
            "Clear the search or choose All.</p></div>")


def where(chunk) -> str:
    doc = re.sub(r"[_-]+", " ", Path(chunk.doc).stem)
    m = re.search(r"#(p|s|row)(\d+)", chunk.chunk_id)
    return f"{doc}, {({'p': 'p. ', 's': 'section ', 'row': 'row '})[m[1]]}{m[2]}" if m else doc


def highlight(text: str, phrases: list[str]) -> str:
    spans = sorted(m.span() for p in phrases if p.split()
                   for m in [re.search(r"(?<!\w)" + r"[\W_]+".join(map(re.escape, p.split())) + r"(?!\w)", text, re.I)] if m)
    out, last = [], 0
    for a, b in spans:
        if a >= last:
            out += [E(text[last:a]), f"<mark>{E(text[a:b])}</mark>"]
            last = b
    return "".join(out) + E(text[last:])


def passage(text: str, phrases: list[str], hints: set[str], width: int = 360) -> str:
    """The part of a long passage that the answer leans on, with the whole passage one click away."""
    if len(text) <= width * 1.5:
        return f"<blockquote>{highlight(text, phrases)}</blockquote>"

    def score(start: int) -> int:
        window = text[start:start + width].lower()
        return sum(len(h) > 0 and re.search(rf"(?<!\w){re.escape(h)}(?!\w)", window) is not None for h in hints)

    start = max(range(0, len(text) - width + 60, 60), key=score)
    start = text.rfind(" ", 0, start) + 1
    end = text.find(" ", start + width)
    end = len(text) if end < 0 else end
    cut = ("… " if start else "") + highlight(text[start:end], phrases) + (" …" if end < len(text) else "")
    return (f"<blockquote>{cut}</blockquote><details><summary>Whole passage</summary>"
            f"<blockquote>{highlight(text, phrases)}</blockquote></details>")


def referral_line(req: dict | None) -> str:
    named = [(t["topic"], t["referral"]) for t in (req or {}).get("must_refuse", [])
             if t.get("referral") and t["referral"] != DEFAULT_REFERRAL]
    if not named:
        return (f"<b>Who can answer:</b> {E(DEFAULT_REFERRAL)}. "
                "Your documents don't name a specific person for this.")
    return "<b>Who can answer:</b> " + "; ".join(f"{E(topic)}: {E(who)}" for topic, who in named)


ZONES = (("quoted", "Quoted", "Words copied from your documents"),
         ("close", "Close to source", "Most of the words are in one passage"),
         ("none", "Unsurveyed", "No source found"))


def render_turn(question: str, turn: Turn, meta: str, req: dict | None, note: str = "") -> tuple[str, str]:
    """(answer, source panel). Support is decided by checks.sentence_support, never by a model."""
    marked = support_of(turn)
    body, boxed = [], False
    if turn.status == "refused":  # a refusal makes no claim, so nothing is hatched
        body.append(f"<p>{E(turn.text)}</p>")
    for sentence, support, chunk, _ in marked:
        if support == "none" and not boxed:
            body.append('<div class="unsurveyed"><span class="lbl">Unsurveyed: no source found</span>'
                        '<span class="help">Check this part yourself before you rely on it.</span>')
        elif support != "none" and boxed:
            body.append("</div>")
        boxed = support == "none"
        word = {"quoted": "Quoted", "close": "Close to source"}.get(support)
        tag = f' <span class="tag tag-{support}">{word} · {E(where(chunk))}</span>' if word else ""
        body.append(f"<p>{E(sentence)}{tag}</p>")
    if boxed:
        body.append("</div>")
    for call in turn.tool_calls:
        args = E(json.dumps(call.args))
        body.append(f'<p class="tool">Used {E(call.name)} {args}</p>' if call.ok else
                    f'<p class="tool">The {E(call.name)} tool failed, so nothing in this answer comes from it: '
                    f"{E(call.result[:200])}</p>")
    who = (f'<p class="who">{referral_line(req)}</p>'
           if turn.status == "refused" or any(m[1] == "none" for m in marked) else "")
    raw = f"<details><summary>Raw turn JSON</summary><pre>{E(turn.model_dump_json(indent=1))}</pre></details>"
    column = (f'<div class="fg box reply">{step(2, "Read the answer")}<h2 class="q">{E(question)}</h2><p class="meta">{meta}</p>{note}'
              f'<div class="answer">{"".join(body)}</div>{who}{raw}<p class="limit">{LIMIT}</p></div>')

    counts = Counter(m[1] for m in marked)
    zones = "".join(f'<li><span class="sw sw-{k}" aria-hidden="true"></span><span><span class="zname">{label}</span>'
                    f'<span class="zhelp">{meaning}</span></span><b>{counts[k]}</b></li>' for k, label, meaning in ZONES)
    phrases: dict[str, list[str]] = {}
    found, hints = {}, {}
    for sentence, support, chunk, match in marked:
        if chunk:
            found.setdefault(chunk.chunk_id, chunk)
            figures = [n for n in NUMBER.findall(sentence) if not re.fullmatch(r"(19|20)\d\d", n)]  # years mark nothing
            phrases.setdefault(chunk.chunk_id, []).extend([match, *figures])
            hints.setdefault(chunk.chunk_id, set()).update(
                [w for w in re.findall(r"\w+", sentence.lower()) if len(w) > 3] + figures)
    texts = {c.chunk_id: c for c in context_chunks(turn)}
    for citation in turn.citations:
        if citation.chunk_id in texts:
            found.setdefault(citation.chunk_id, texts[citation.chunk_id])
            phrases.setdefault(citation.chunk_id, []).append(citation.quote)
            hints.setdefault(citation.chunk_id, set()).update(re.findall(r"\w{4,}", citation.quote.lower()))
    passages = "".join(f'<li><p class="from">{E(where(c))}</p>'
                       f'{passage(c.text, phrases[c.chunk_id], hints.get(c.chunk_id, set()))}</li>'
                       for c in found.values())
    panel = (f'<div class="fg sources">{step(3, "Check the source")}<ul class="zones">{zones}</ul>'
             + (f'<ul class="passages">{passages}</ul>' if passages else
                '<p class="muted">No passage supports this answer.</p>') + "</div>")
    return column, panel


def no_sources(text: str = "Nothing to show.") -> str:
    return f'<div class="fg sources">{step(3, "Check the source")}<p class="muted">{E(text)}</p></div>'


def empty_chat(d: dict, live: bool) -> tuple[str, str]:
    if d["agent"] is None:
        how = "This run has no agent yet. Watch it on the Factory log page."
    elif live:
        how = "Type your question in the box at the top. I'll mark where every sentence came from."
    else:
        how = "This run recorded no answers, and no model is connected."
    return (f'<div class="fg box reply">{step(2, "Read the answer")}<p class="muted">{how}</p></div>',
            no_sources("Nothing asked yet."))


def replay(d: dict, case_id: str) -> tuple[str, str]:
    result = d["results"][case_id]
    reasons = result.reasons or [*result.unsupported, *result.missing_facts]
    why = " ".join(_short(plain(r), 200) for r in reasons[:2])
    split = "hidden" if d["split"][case_id] == "sealed" else "practice"
    meta = f'{outcome(result.state)} · {split} test question {E(case_id)} · answer saved during the test'
    note = (f'<p class="reason is-{result.state}"><b>Why {"it failed" if result.state == "failed" else "nobody can say"}:'
            f"</b> {E(why)}</p>" if why and result.state != "passed" else "")
    return render_turn(question_of(d, case_id), result.turn, meta, d["req"], note)


# --- factory log: one row per stage, read from the file that stage wrote ---


def _details(path: Path) -> str:
    if not path.is_file():
        return ""
    text = path.read_text()
    return (f"<details><summary>{E(path.name)}</summary><pre>{E(text[:6000])}"
            f"{E(chr(10) + '(cut; open the file for the rest)') if len(text) > 6000 else ''}</pre></details>")


def _meters(entry: dict) -> str:
    found = ((label, re.match(r"(\d+)/(\d+)", entry.get(key) or ""))
             for label, key in (("Before", "train_before"), ("After", "train_after")))
    return "".join(f'<span class="meterline">{label}<span class="meter" '
                   f'style="--w:{100 * int(m[1]) / max(int(m[2]), 1):.0f}%" aria-hidden="true"></span>{m[1]} of {m[2]}</span>'
                   for label, m in found if m) or chip("After: not run")


def _fix_words(entry: dict) -> str:
    """The factory's own sentence about a fix, with its two jargon words swapped."""
    said = entry.get("summary", "").replace(f"Refit {entry['refit']}'s", "Its").replace(f"Refit {entry['refit']}", "It")
    return said.replace("Train passes", "Practice passes")


def stage_rows(d: dict) -> list[dict]:
    """One entry per step reached: what it does in plain words, what happened this time, and the file to check."""
    run, card = d["dir"], d["card"]
    rows = []

    def add(number, title, name, yard, happened, chips="", file=""):
        rows.append({"n": number, "title": title, "name": name, "yard": yard, "happened": happened, "chips": chips,
                     "file": file})

    interview, inv = _json(run / "interview.json"), d["inventory"]
    if interview is not None:
        read = sum(doc["read"] for doc in inv)
        assumed = sum(r["source"] == "default" for r in interview)
        add(1, "Ask what you need", "Intake", "Owner's Spec",
            f"I read {read} of {_n(len(inv), 'document')} and asked {_n(len(interview), 'question')}. "
            f"{assumed} got no reply, so I wrote down my guess as an assumption.",
            file=_details(run / "interview.json"))
    table = _json(run / "groundability.json")
    if table is not None:
        v = Counter(r["verdict"] for r in table)
        demoted = [r["topic"] for r in table if r["verdict"] == "unsupported"]
        add(2, "Check the documents can answer it", "Groundability", "Load Line",
            f"I checked {_n(len(table), 'topic')} against your documents."
            + (f" These aren't covered, so the agent refuses them: {', '.join(demoted)}." if demoted else
               " All are covered."),
            chip(f"{v['supported']} covered") + chip(f"{v['partial']} partly") + chip(f"{v['unsupported']} not covered"),
            _details(run / "groundability.json"))
    if d["agent"] is not None:
        tools = [t["name"] for t in d["agent"].get("tools", [])]
        defects = _json(run / "generator_log.json", [])
        add(3, "Write the agent's instructions", "Generator", "Drawing Office",
            (f"It can use: {', '.join(tools)}." if tools else "It needs no tools.")
            + (f" My code corrected the draft {_n(len(defects), 'time')}." if defects else " The draft needed no changes."),
            file=_details(run / "agent.v0.yaml") + (_details(run / "generator_log.json") if defects else ""))
    if d["cases"]:
        rejected = len(_lines(run / "evalset.rejected.jsonl"))
        sides = {k: len(v) for k, v in _json(run / "split.json", {}).items() if isinstance(v, dict)}
        add(4, "Write test questions", "Evalgen", "Sea Trials",
            f"I wrote questions from your documents, kept {len(d['cases'])} and threw out {rejected} weak ones. "
            f"{sides.get('sealed', '?')} stay hidden for the final test.",
            chip(f"{sides.get('train', '?')} practice") + chip(f"{sides.get('sealed', '?')} hidden"),
            _details(run / "evalset.jsonl"))
    canaries = _json(run / "canaries.json")
    if canaries is not None:
        missed = [CANARIES.get(c["name"], c["name"]) for c in canaries if not c["ok"]]
        add(5, "Test the grader", "Judge", "Survey",
            "I gave the grader answers whose right verdict I already knew. "
            + (f"It missed {', '.join(missed)}, so its verdicts count as unknown." if missed else "It got them all right."),
            outcome("failed" if missed else "passed") + chip(f"{len(canaries) - len(missed)} of {len(canaries)}"),
            _details(run / "canaries.json"))
    if d["log"]:
        tries = "".join(
            f'<li><p><b>Fix {e["refit"]}: {"kept" if e.get("accepted") else "put back"}.</b> {E(_fix_words(e))}</p>'
            f'<p class="meters">{_meters(e)}</p><details><summary>Show the change</summary>'
            f"<pre>{E(json.dumps(e, indent=1))}</pre></details></li>" for e in d["log"])
        kept = sum(bool(e.get("accepted")) for e in d["log"])
        add(6, "Try to fix what failed", "Refit", "Refit",
            f"I tried {len(d['log'])} fix{'es' * (len(d['log']) != 1)} and kept {kept}. A fix stays only if it helps more "
            "than luck would.", file=f'<ol class="tries">{tries}</ol>')
    if card is not None:
        sealed = card["sealed"]["final"]
        add(7, "Write the report card", "Report", "Certificate",
            (f"On the hidden test: {report.headline(sealed)}. " if sealed else "The hidden test never ran. ")
            + f"{len(card['failures'])} questions are still open.", file=_details(run / "scorecard.json"))
    if (run / "agent.final.yaml").is_file() and card is not None:
        add(8, "Ready to answer", "Ready", "Bridge",
            f"Ask it on the first page, or run: forge chat {run.name}/agent.final.yaml")
    return rows


def _state_block(run: Path) -> str:
    state = jobs.state(run)
    if state == "finished":
        return '<p class="lead">Every step this agent went through, in order. Each one is read from a file it wrote.</p>'
    said = {"running": "Running. I re-read the run folder every 3 seconds. Closing this page doesn't stop the run.",
            "not_groundable": "Stopped: the documents can't support this brief. The report says why.",
            "stopped": f"Stopped before the end. Resume it here, or run: forge resume {run}. Finished model calls are reused.",
            "outside": "Not finished. It was started outside this page, so I can't tell whether it's still running."}[state]
    tail = run / ("report.md" if state == "not_groundable" else jobs.LOG)
    text = tail.read_text(errors="replace") if tail.is_file() else ""
    shown = text[:4000] if state == "not_groundable" else "\n".join(text.splitlines()[-12:])
    return (f'<p class="notice" role="status">{E(said)}</p>'
            + (f'<pre tabindex="0" aria-label="{E(tail.name)}">{E(shown)}</pre>' if shown else ""))


def _agent_name(d: dict) -> str:
    return (d["agent"] or {}).get("name") or "Agent not built yet"


def log_html(d: dict) -> str:
    steps = "".join(
        f'<li><b class="num" aria-hidden="true">{r["n"]}</b><div><h3>{E(r["title"])}</h3><p class="tech">{E(r["name"])} · '
        f'<i>{E(r["yard"])}</i></p></div><div class="did"><p>{E(r["happened"])}</p>'
        + (f'<p class="chips">{r["chips"]}</p>' if r["chips"] else "") + f'{r["file"]}</div></li>'
        for r in stage_rows(d))
    return (f'<div class="fg page-doc logpage"><h2>How it was built</h2><p class="who-for">{E(_agent_name(d))}</p>'
            f'{_state_block(d["dir"])}'
            + (f'<ol class="steps">{steps}</ol>' if steps else '<p class="muted">No step has finished yet.</p>') + "</div>")


# --- report card ---


def certificate_html(d: dict, interactive: bool = True) -> str:
    card = d["card"]
    if card is None:
        return say("This run isn't finished, so there's no report card yet.")
    m, b = models(d), card["budget"]
    missed, total = _missed(card), len(card["judge"]["canaries"])
    grader = (f'<p class="answer-big st-failed">{mark("failed")}Not fully.</p><p class="warn">The grader got {total - len(missed)} '
              f'of {total} planted answers right. It missed {E(", ".join(missed))}, so every verdict that depends on the '
              "model is unknown.</p>" if missed else
              f'<p class="answer-big st-passed">{mark("passed")}Yes, on this check.</p><p>Judge self-test: it graded '
              f"{total} of {total} planted answers correctly. These were answers whose right verdict I already knew.</p>")
    warns = "".join(f'<p class="warn">{E(w)}</p>' for w in report.warnings(card) if "JUDGE" not in w.upper())
    sealed = card["sealed"]["final"]
    score = (f'{_bar(sealed)}<p class="verdicts big-verdicts">{_verdicts(sealed)}</p><p>{E(_rate(card))}</p>'
             "<p>These are the hidden questions. The fixer never saw them.</p>" if sealed else
             "<p>The hidden test never ran.</p>")
    tag, act = ("button", 'type="button"') if interactive else ("span", "")

    def area(split: str, title: str) -> str:
        ids = sorted(i for i in d["results"] if d["split"][i] == split)
        cells = "".join(
            f'<li><{tag} {act} class="cell is-{d["results"][i].state}" data-case="{E(i)}">{mark(d["results"][i].state)}'
            f'<span>{E(i)}</span><span class="sr-only">, {d["results"][i].state}</span></{tag}></li>' for i in ids)
        return f'<div><h4>{title}: {len(ids)} questions</h4><ul class="cells">{cells}</ul></div>'

    kinds = Counter(f["category"] for f in card["failures"])
    overview = "".join(f'<li><b>{n}</b><span>{E(PROBLEM.get(k, k.replace("_", " ")))}</span></li>'
                       for k, n in kinds.most_common())

    def why(f: dict) -> str:
        return plain(f["evidence"]) if f["evidence"] else "No evidence was saved."

    still = "".join(
        f'<li><div><p class="q2">{E(f["question"])}</p><p class="small is-{_state_of(d, f["id"])}">'
        f'{mark(_state_of(d, f["id"]))}{_state_of(d, f["id"]).capitalize()} · '
        f'{E(PROBLEM.get(f["category"], f["category"]))} · {E(f["id"])}</p><p><b>What happened:</b> {E(why(f))}</p>'
        f'<p><b>Try next:</b> {E(NEXT_STEP.get(f["category"], "Read the answer and the passage it cites."))}</p>'
        f'<details><summary>For engineers</summary><pre>{E(f["split"])} · {E(f["category"])}\n{E(f["evidence"])}\n'
        f'{E(f["still_open_because"])}</pre></details></div>'
        + (f'<button type="button" class="open" data-case="{E(f["id"])}">Read answer'
           f'<span class="sr-only"> {E(f["id"])}</span></button>' if interactive else "") + "</li>"
        for f in card["failures"]) or "<li><div><p>Nothing is open.</p></div></li>"
    refits = "".join(
        f'<li><div><p><b>Fix {e["refit"]}: {"kept" if e.get("accepted") else "put back"}.</b> {E(_fix_words(e))}</p>'
        f'<p class="meters">{_meters(e)}</p></div></li>' for e in d["log"]) or "<li><div><p>No fix was tried.</p></div></li>"
    facts = "".join(f"<div><dt>{label}</dt><dd>{E(str(value))}</dd></div>" for label, value in (
        ("Run", d["dir"].name), ("Builder model", m.get("builder", "?")), ("Grader model", m.get("examiner", "?")),
        ("Model calls", b["calls"]), ("Tokens", f"{b['tokens']:,}")))
    check, files = doc_check(d)
    documents = "".join(f'<tr><th scope="row">{E(name)}</th><td><code>{E(sha[:12])}</code></td><td>{E(status)}</td></tr>'
                        for name, sha, status in files)
    hint = "<p>Press a question to read its answer.</p>" if interactive else ""
    return (f'<div class="fg page-doc certificate"><h2>Report card</h2><p class="who-for">{E(card["name"])}</p>'
            '<p class="lead">How good is this agent, and what still goes wrong?</p>'
            f'<section><h3>Can you trust the grader?</h3>{grader}{warns}</section>'
            f'<section><h3>How did the agent do?</h3>{score}</section>'
            f'<section><h3>What still goes wrong?</h3><ul class="kinds">{overview}</ul><ol class="list">{still}</ol></section>'
            f'<section><h3>Every test question</h3>{hint}<div class="areas">{area("sealed", "Hidden test")}'
            f'{area("train", "Practice")}</div></section>'
            f'<section><h3>Fixes the factory tried</h3><ol class="list">{refits}</ol></section>'
            f'<section><h3>Details for engineers</h3><dl class="register">{facts}</dl>'
            + (f'<div class="scroll"><table><caption>Documents tested</caption><thead><tr><th scope="col">File</th>'
               '<th scope="col">SHA-256 (first 12)</th><th scope="col">Now</th></tr></thead>'
               f'<tbody>{documents}</tbody></table></div>' if documents else "")
            + '</section><p class="closing">Unknown is not zero. I count unknown questions apart.</p></div>')


def _state_of(d: dict, case_id: str) -> str:
    return d["results"][case_id].state if case_id in d["results"] else "unknown"
