"""forge ui: Ask a question, Report card, How it was built and Build a new agent, all read from the files a run writes.

The UI never runs the pipeline in its own process (jobs.py starts `forge build`). Replay needs no model
and no key; live chat and new runs need --config. HTML comes from views.py, style from ui.css.
The page fetches nothing from outside and Gradio's analytics are off.
"""

import base64
import tempfile
import time
import traceback
from pathlib import Path

from . import jobs
from .inventory import SUPPORTED
from .views import (E, _json, case_list, case_order, certificate_html, chip, empty_chat, hero, list_runs, load,
                    log_html, no_sources, render_turn, replay, run_choices, say, step, trust)

CHAT_LIMITS = {"timeout": 60, "attempts": 2}  # a person is waiting; a build may retry for minutes
LATIN = ("U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,"
         "U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD")
LATIN_EXT = ("U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,"
             "U+20A0-20AB,U+20AD-20C4,U+2113,U+2C60-2C7F,U+A720-A7FF")
SYMBOLS = "U+2190,U+2192,U+2194-21FF,U+2200-2211,U+2215-22FF,U+25A0-25FF"
FACES = (("Public Sans", "400 700", "normal", "public-sans-latin", LATIN),
         ("Public Sans", "400 700", "normal", "public-sans-latin-ext", LATIN_EXT),
         ("Public Sans", "400 700", "italic", "public-sans-italic-latin", LATIN),
         ("Public Sans", "400 700", "italic", "public-sans-italic-latin-ext", LATIN_EXT),
         ("IBM Plex Mono", "400", "normal", "ibm-plex-mono-400-latin", LATIN),
         ("IBM Plex Mono", "400", "normal", "ibm-plex-mono-400-symbols", SYMBOLS))


def _css() -> str:
    """ui.css plus its fonts as data URIs: no font request leaves the machine, and a saved certificate keeps its type."""
    here = Path(__file__).parent
    faces = []
    for family, weight, style, stem, span in FACES:
        data = base64.b64encode((here / "fonts" / f"{stem}.woff2").read_bytes()).decode()
        faces.append(f'@font-face{{font-family:"{family}";font-weight:{weight};font-style:{style};font-display:swap;'
                     f'src:url(data:font/woff2;base64,{data}) format("woff2");unicode-range:{span}}}')
    return "\n".join(faces) + "\n" + (here / "ui.css").read_text()


CSS = _css()

# in the browser: search and verdict filters stay local, a row click asks Python for that recorded answer
LIST_JS = """
const apply = () => {
  const pressed = element.querySelector('[data-filter][aria-pressed="true"]'), box = element.querySelector('[data-search]');
  if (!pressed || !box) return;
  const words = box.value.trim().toLowerCase();
  let shown = 0;
  element.querySelectorAll('li[data-tags]').forEach(li => {
    const ok = (pressed.dataset.filter === 'all' || li.dataset.tags.split(' ').includes(pressed.dataset.filter))
      && li.dataset.text.includes(words);
    li.hidden = !ok; shown += ok;
  });
  element.querySelector('[data-empty]').hidden = shown > 0;
};
element.addEventListener('input', apply);
// a new list (another agent, or a case opened from the certificate) starts unfiltered
watch('value', () => {
  const box = element.querySelector('[data-search]');
  if (box) box.value = '';
  element.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', b.dataset.filter === 'all'));
  apply();
  element.querySelector('[data-case][aria-pressed="true"]')?.scrollIntoView({block: 'nearest'});
});
element.addEventListener('click', event => {
  const filter = event.target.closest('[data-filter]');
  if (filter) {
    element.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', b === filter));
    apply(); return;
  }
  const row = event.target.closest('[data-case]');
  if (!row) return;
  element.querySelectorAll('[data-case]').forEach(b => b.setAttribute('aria-pressed', b === row));
  trigger('click', {picked: row.dataset.case});
});
"""
OPEN_JS = """
element.addEventListener('click', event => {
  const hit = event.target.closest('button[data-case]');
  if (hit) trigger('click', {picked: hit.dataset.case});
});
"""
# a button inside our own HTML that opens another page, by pressing that page's button in the rail
GOTO_JS = """
element.addEventListener('click', event => {
  const hit = event.target.closest('[data-goto]');
  if (hit) document.querySelector('button.nav-' + hit.dataset.goto)?.click();
});
"""
# bring the answer into view only when it is off screen (phones, or opened from far down a page)
SHOW_ANSWER = """() => { setTimeout(() => { const q = document.querySelector('#answer .reply'); if (!q) return;
  const top = q.getBoundingClientRect().top;
  if (top < 0 || top > innerHeight * 0.7) q.scrollIntoView({block: 'start',
    behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}); }, 60); }"""
PAGES = (("ask", "Ask a question"), ("certificate", "Report card"), ("log", "How it was built"), ("new", "Build a new agent"))


def page_js(page: str) -> str:
    """Pages are all in the DOM and CSS shows one, so switching is instant and nothing is re-read."""
    return f"""() => {{ document.body.dataset.page = '{page}';
      document.querySelectorAll('button.nav').forEach(b =>
        b.setAttribute('aria-current', b.classList.contains('nav-{page}') ? 'page' : 'false'));
      scrollTo({{top: 0}}); }}"""


KEY = ('<div class="fg key"><h2>What the colours mean</h2><ul>'
       + "".join(f'<li><span class="k k-{name}" aria-hidden="true"></span>{meaning}</li>' for name, meaning in (
           ("source", "From your documents"), ("none", "No source found"), ("passed", "Passed"), ("failed", "Failed"),
           ("unknown", "Unknown"), ("act", "A button to press")))
       + "</ul></div>")


def certificate_file(d: dict) -> str:
    """The same HTML as the page, as one standalone file, so screen and paper can't disagree."""
    path = Path(tempfile.gettempdir()) / f"forge-certificate-{d['dir'].name}.html"
    path.write_text(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
                    f"content='width=device-width'><title>Certificate: "
                    f"{E(d['card']['name'] if d['card'] else d['dir'].name)}</title><style>{CSS}"
                    "body{background:var(--ground);margin:48px auto;max-width:60rem;padding:0 24px}</style></head>"
                    f"<body>{certificate_html(d, interactive=False)}</body></html>")
    return str(path)


class Live:
    """Live chat against the builder model of one config, with the same run_turn() the evals use."""

    def __init__(self, path: Path):
        from .index import Embedder
        from .llm import LLM, load_config
        self.path = Path(path)
        self.config = load_config(self.path)
        chat = {**self.config, "builder": {**self.config["builder"], **CHAT_LIMITS}}
        self.llm = LLM(chat)
        self.embed = Embedder(self.config["embeddings"]["model"])
        self.indexes: dict = {}
        self.model = self.config["builder"]["model"]

    def answer(self, run_dir: Path, question: str) -> tuple[str, str]:
        from .index import Index
        from .inventory import scan
        from .runtime import load_agent, run_turn, stale_documents
        path = run_dir / "agent.final.yaml"
        if not path.is_file():
            return say("This run has no agent yet. Open How it was built to watch it."), no_sources()
        started = time.monotonic()
        try:
            agent = load_agent(path)
            key = (str(run_dir), tuple(sorted(agent.documents.items())))
            if key not in self.indexes:
                folder = (path.resolve().parent / agent.docs_dir).resolve()
                docs = scan(folder)
                stale = stale_documents(agent, docs)
                if stale:
                    return say(f"The documents changed since this agent was tested ({', '.join(stale)}), so its scores "
                               "no longer apply and live chat is off for it. Run forge chat with --reindex if you "
                               "want it anyway."), no_sources()
                self.indexes[key] = Index(docs, self.embed, folder)
            turn = run_turn(self.llm, agent, self.indexes[key], question)
        except Exception as e:  # shown to the person who asked; the traceback goes to the terminal
            traceback.print_exc()
            return say(f"No answer: {str(e)[:300]}. Nothing was saved. Send the question again to retry."), no_sources()
        meta = f"Live answer from {E(self.model)} · {time.monotonic() - started:.0f} s · nobody has judged it"
        return render_turn(question, turn, meta, _json(run_dir / "requirements.final.json"))


def build_app(root: Path, config: Path | None = None):
    import gradio as gr

    root = Path(root).resolve()
    live = Live(config) if config else None

    def folder(name) -> Path | None:
        return root / name if name in list_runs(root) else None  # the browser sends the name, so check it

    def select(name):
        try:
            return page_of(name)
        except Exception as e:  # half-written or older files: say which run and what to do, keep the rest working
            traceback.print_exc()
            broken = say(f"I couldn't read the run {name} ({type(e).__name__}). Its files may be half written or from "
                         "an older version. Choose another agent, or read the terminal for the details.")
            hidden = gr.update(visible=False)
            return [broken, "", "", broken, no_sources(), broken, broken, hidden, hidden, hidden, *[hidden] * 3]

    def page_of(name):
        run = folder(name)
        if run is None:
            empty = say("No agents yet. Open Build a new agent, or run forge build in a terminal.")
            hidden = gr.update(visible=False)
            return ["", "", "", empty, no_sources(), empty, empty, hidden, hidden, hidden, *[hidden] * 3]
        d = load(run)
        state = jobs.state(run)
        first = next(iter(case_order(d)), None)  # open on a real answer, never an empty page
        column, panel = replay(d, first) if first else empty_chat(d, bool(live))
        topics = (d["req"] or {}).get("must_answer", []) if live and d["agent"] else []
        examples = [gr.update(value=topics[i]["example_question"], visible=True) if i < len(topics)
                    else gr.update(visible=False) for i in range(3)]
        return [hero(d, live.model if live else None), trust(d), case_list(d, first), column, panel,
                log_html(d), certificate_html(d),
                gr.update(value=certificate_file(d) if d["card"] else None, visible=bool(d["card"])),
                gr.update(visible=bool(live) and state == "running"),
                gr.update(visible=bool(live) and state == "stopped"), *examples]

    def seen(name):
        run = folder(name)
        return (jobs.state(run), log_html(load(run))) if run else ("", "")

    def recorded(name, case_id):
        run = folder(name)
        d = load(run) if run else None
        return d if d and case_id in d["results"] else None

    def pick(name, event: gr.EventData):
        d = recorded(name, event.picked)
        return replay(d, event.picked) if d else (gr.skip(), gr.skip())

    def open_case(name, event: gr.EventData):
        d = recorded(name, event.picked)
        if not d:
            return gr.skip(), gr.skip(), gr.skip()
        return (case_list(d, event.picked, time.monotonic_ns()), *replay(d, event.picked))

    def ask(name, question):
        run, question = folder(name), (question or "").strip()
        if not (run and question):
            yield say("Type a question first."), gr.skip()
            return
        yield (f'<div class="fg box reply">{step(2, "Read the answer")}<h2 class="q">{E(question)}</h2><p class="meta" role="status">Asking '
               f"{E(live.model)}. The first question also reads the documents, so it takes longer.</p></div>",
               no_sources("Waiting for the answer."))
        yield live.answer(run, question)

    def tick(name, last):
        run = folder(name)
        now = seen(name)
        if run is None or now == tuple(last):
            return [gr.skip()] * (len(outputs) + 1)  # nothing new, so open details stay open
        if now[0] != last[0]:  # started, stopped or finished: redraw every page
            return [now, *select(name)]
        return [now, *[now[1] if o is log else gr.skip() for o in outputs]]

    def start(brief, files):
        try:
            name = jobs.start(root, brief, files, live.path)
        except (ValueError, OSError) as e:
            return say(str(e)), gr.skip()
        return (f'<div class="fg box ok"><p role="status">Started run {E(name)}.</p></div>',
                gr.update(choices=run_choices(root), value=name))

    def control(action, name):
        run = folder(name)
        if run:
            try:
                action(run)
            except (ValueError, OSError) as e:
                gr.Warning(str(e))

    def refresh(name):
        runs = list_runs(root)
        return gr.update(choices=run_choices(root), value=name if name in runs else (runs[0] if runs else None))

    def html(**kwargs):
        return gr.HTML(apply_default_css=False, **kwargs)

    def head(title: str, text: str) -> str:
        return f'<div class="fg pagehead"><h2>{title}</h2><p class="muted">{text}</p></div>'

    runs = list_runs(root)
    first = next((r for r in runs if jobs.state(root / r) == "finished"), runs[0] if runs else None)

    with gr.Blocks(title="ForgeAI", fill_width=True, analytics_enabled=False) as demo:
        with gr.Row(elem_classes="shell"):
            with gr.Column(elem_classes="side", min_width=0):
                html(value='<div class="fg brand"><h1>ForgeAI</h1><p>It makes an assistant from your documents, then tests it.</p></div>')
                with gr.Column(elem_classes="navs"):
                    navs = [gr.Button(label, elem_classes=["nav", f"nav-{key}"]) for key, label in PAGES]
                picker = gr.Radio(run_choices(root), value=first, label="Which agent?", elem_classes="agents")
                html(value=KEY)
                night = gr.Button("Night mode on or off", elem_classes="theme")
            with gr.Column(elem_classes="main", min_width=0):
                top = html(elem_classes="hero-wrap")
                cards = html(elem_classes=["page", "page-ask"], js_on_load=GOTO_JS)
                with gr.Row(elem_classes=["page", "page-ask", "askbar"], visible=bool(live)):
                    question = gr.Textbox(label="Your question", show_label=False, lines=1, max_lines=4,
                                          max_length=1000, placeholder="Type your own question here",
                                          container=False, min_width=0)
                    send = gr.Button("Send question", variant="primary", scale=0, min_width=170)
                with gr.Row(elem_classes=["page", "page-ask", "suggest"], visible=bool(live)):
                    examples = [gr.Button(visible=False, elem_classes="example", min_width=0, scale=0) for _ in range(3)]
                with gr.Row(elem_classes=["page", "page-ask", "desk"]):
                    with gr.Column(elem_classes="col-list", min_width=0):
                        cases = html(js_on_load=LIST_JS)
                    with gr.Column(elem_classes="col-answer", min_width=0):
                        answer = html(elem_id="answer")
                    with gr.Column(elem_classes="col-sources", min_width=0):
                        sources = html()
                with gr.Column(elem_classes=["page", "page-log"]):
                    with gr.Row(elem_classes="actions"):
                        halt = gr.Button("Stop this run", visible=False, scale=0, min_width=180)
                        again = gr.Button("Resume this run", variant="primary", visible=False, scale=0, min_width=200)
                    log = html()
                with gr.Column(elem_classes=["page", "page-certificate"]):
                    cert = html(js_on_load=OPEN_JS)
                    with gr.Row(elem_classes="actions"):
                        download = gr.DownloadButton("Download certificate", variant="primary", visible=False,
                                                     scale=0, min_width=240)
                with gr.Column(elem_classes=["page", "page-new"]):
                    if live:
                        examiner = live.config["examiner"]["model"]
                        slow = (" This setup is rate-limited, so a full run takes hours."
                                if live.config["builder"].get("rpm") else "")
                        html(value=head("Build a new agent", "Give me one paragraph and your documents. I'll build the agent, "
                                        "test it, and tell you what still fails."))
                        with gr.Row(elem_classes="form"):
                            with gr.Column(elem_classes="step-card", min_width=0):
                                brief = gr.Textbox(label="1. Say what the agent should do, in one paragraph", lines=7,
                                                   max_length=4000,
                                                   placeholder="I need an assistant that answers ... using these documents.")
                            with gr.Column(elem_classes="step-card", min_width=0):
                                files = gr.File(label=f"2. Add your documents ({', '.join(SUPPORTED)})",
                                                file_count="multiple", file_types=list(SUPPORTED), type="filepath",
                                                height=200)
                        html(value=f'<div class="fg note"><p><b>Your documents are sent to {E(live.model)} and '
                             f'{E(examiner)}</b> at the addresses in {E(live.path.name)}. Free tiers may train on what '
                             f'you send, so use public or synthetic documents there.</p><p>The run is unattended: I record '
                             f'each intake default as an assumption. To answer the questions yourself, use '
                             f'<code>forge build</code> in a terminal.{slow} PDFs need selectable text. The run keeps going if you close '
                             f'this page.</p></div>')
                        with gr.Row(elem_classes="actions"):
                            begin = gr.Button("3. Build my agent", variant="primary", scale=0, min_width=220)
                        started = html(elem_id="started")
                    else:
                        html(value=head("Build a new agent", "No model is connected, so this copy can only show saved runs.")
                             + '<div class="fg box"><p>To build from your own brief and documents, restart with a model '
                             "config:</p><pre>uv run forge ui --config forge.toml</pre></div>")
                html(value='<p class="fg foot">I read every number on this page from the files a run wrote.</p>')

        outputs = [top, cards, cases, answer, sources, log, cert, download, halt, again, *examples]
        last = gr.State(("", ""))
        demo.load(None, js=page_js("ask"))
        demo.load(refresh, picker, picker).then(select, picker, outputs).then(seen, picker, last)
        picker.change(select, picker, outputs).then(seen, picker, last)
        for button, (key, _) in zip(navs, PAGES):
            button.click(None, js=page_js(key))
        cases.click(pick, picker, [answer, sources]).then(None, js=SHOW_ANSWER)
        cert.click(open_case, picker, [cases, answer, sources]).then(None, js=page_js("ask")).then(None, js=SHOW_ANSWER)
        if live:
            for asked in (send.click, question.submit):
                asked(ask, [picker, question], [answer, sources], trigger_mode="once").then(None, js=SHOW_ANSWER)
            for button in examples:
                button.click(lambda text: text, button, question).then(
                    ask, [picker, question], [answer, sources]).then(None, js=SHOW_ANSWER)
            begin.click(start, [brief, files], [started, picker], trigger_mode="once").then(
                None, js=f"() => {{ if (document.querySelector('#started .ok')) ({page_js('log')})(); }}")
            halt.click(lambda name: control(jobs.stop, name), picker)
            again.click(lambda name: control(lambda run: jobs.resume(run, live.path), name), picker)
        night.click(None, js="() => document.body.classList.toggle('dark')")
        demo.load(None, js="() => document.getElementById('answer')?.setAttribute('aria-live', 'polite')")
        gr.Timer(3).tick(tick, [picker, last], [last, *outputs], show_progress="hidden")
    return demo


def theme():
    import gradio as gr
    pairs = {  # day, night. The same pigments as ui.css
        "body_background_fill": ("#f5f6f8", "#0b1120"), "background_fill_primary": ("#ffffff", "#111827"),
        "background_fill_secondary": ("#eef1f5", "#1a2438"), "body_text_color": ("#111827", "#f1f5f9"),
        "body_text_color_subdued": ("#525d70", "#94a3b8"), "block_title_text_color": ("#111827", "#f1f5f9"),
        "block_label_text_color": ("#111827", "#f1f5f9"), "border_color_primary": ("#e2e6ee", "#23304a"),
        "border_color_accent": ("#1d4ed8", "#60a5fa"), "color_accent_soft": ("#eff6ff", "#172554"),
        "input_background_fill": ("#ffffff", "#111827"), "input_border_color": ("#cbd2df", "#364766"),
        "input_border_color_focus": ("#1d4ed8", "#60a5fa"), "link_text_color": ("#1d4ed8", "#60a5fa"),
        "button_secondary_background_fill": ("#ffffff", "#111827"),
        "button_secondary_text_color": ("#111827", "#f1f5f9"),
        "button_secondary_background_fill_hover": ("#eff6ff", "#172554"),
        "button_secondary_border_color": ("#cbd2df", "#364766")}
    for name, day, night in (("background_fill", "#e5a00d", "#f5b92a"), ("background_fill_hover", "#f2b224", "#f9c84d"),
                             ("text_color", "#0f172a", "#0f172a"), ("text_color_hover", "#0f172a", "#0f172a"),
                             ("border_color", "#d4920a", "#f5b92a")):
        pairs[f"button_primary_{name}"] = (day, night)  # signal amber: the one thing to press, day or night
    tokens = {name: day for name, (day, _) in pairs.items()}
    tokens |= {f"{name}_dark": night for name, (_, night) in pairs.items()}
    font = gr.themes.Font  # local names only: ui.css carries the files, so nothing is fetched from a font host
    return gr.themes.Base(font=[font("Public Sans"), font("system-ui"), font("sans-serif")],
                          font_mono=[font("IBM Plex Mono"), font("monospace")],
                          radius_size=gr.themes.sizes.radius_md).set(
        color_accent="#1d4ed8", block_background_fill="transparent", block_background_fill_dark="transparent",
        block_border_width="0px", block_shadow="none", input_shadow="none", input_border_width="1px",
        block_label_background_fill="transparent", block_title_background_fill="transparent",
        block_padding="0px", layout_gap="14px", button_border_width="1px", button_large_radius="8px",
        button_medium_radius="8px", button_large_padding="11px 20px", button_large_text_weight="700",
        button_medium_text_weight="600", block_title_text_weight="700", **tokens)


def launch(root: Path, config: Path | None = None, port: int | None = None) -> int:
    # with a model connected, anyone who can open the page can spend its keys, so it stays on this machine
    local = {"server_name": "127.0.0.1", "share": False} if config else {}
    build_app(root, config).launch(theme=theme(), css=CSS, server_port=port, max_file_size="25mb",
                                   footer_links=[], **local)
    return 0
