"""Folder scan and loaders. Every file is listed; anything unreadable is marked, never skipped silently."""

import csv
import hashlib
import io
import re
from pathlib import Path

from pydantic import BaseModel

SUPPORTED = {".pdf": "pdf", ".docx": "docx", ".csv": "csv", ".md": "md", ".txt": "txt"}
HEADING = re.compile(
    r"^(#{1,6}\s+.+"
    r"|(Regulation|Standard|Guideline|Title|Section|Article|Chapter|Part|Clause)\s+[A-Z0-9][\w.\-]*.{0,80}"
    r"|\d+(\.\d+)*\.?\s+[A-Z][^.:,;]{0,50}"
    r"|[A-Z][A-Z0-9 ,&'/\-]{5,60})$"
)
MIN_CHARS_PER_PAGE = 40  # below this a PDF has no usable text layer
LINE_HYPHEN = re.compile(r"(?<=[A-Za-z]) ?-[ \t]*\n[ \t]*(?=[a-z])")  # "communi -\ncated" breaks quote matching


class Segment(BaseModel):
    section: str
    text: str


class Doc(BaseModel):
    name: str
    type: str
    sha256: str
    pages: int | None = None
    rows: int | None = None
    headings: list[str] = []
    columns: list[str] = []
    read: bool = True
    note: str = ""
    segments: list[Segment] = []
    records: list[dict[str, str]] = []


def _split_headings(lines: list[str], section: str) -> tuple[list[Segment], list[str]]:
    segments, headings, current, count = [], [], [], 0
    for line in lines:
        stripped = line.strip()
        if HEADING.match(stripped):
            # a very short section (a title, a lone heading) stays with what follows it
            if len(" ".join(current).split()) >= 40:
                count += 1
                segments.append(Segment(section=f"{section}{count}", text="\n".join(current)))
                current = []
            headings.append(stripped.lstrip("# ").strip())
        current.append(line.rstrip())
    if "".join(current).strip():
        count += 1
        segments.append(Segment(section=f"{section}{count}", text="\n".join(current)))
    return segments, headings


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _load(path: Path, doc: Doc) -> None:
    if doc.type == "pdf":
        from pypdf import PdfReader

        texts = [LINE_HYPHEN.sub("", page.extract_text() or "") for page in PdfReader(path).pages]
        doc.pages = len(texts)
        if sum(len(t.strip()) for t in texts) < MIN_CHARS_PER_PAGE * max(len(texts), 1):
            doc.read, doc.note = False, "no text layer (scanned PDF?); no OCR"
            return
        empty = [i for i, t in enumerate(texts, 1) if not t.strip()]
        if empty:
            doc.note = f"pages with no text, not read: {', '.join(map(str, empty))}"
        for number, text in enumerate(texts, 1):
            segments, headings = _split_headings(text.splitlines(), f"p{number}.")
            doc.segments += segments
            doc.headings += headings
    elif doc.type == "docx":
        from docx import Document

        document = Document(path)
        lines = []
        for block in document.iter_inner_content():
            if hasattr(block, "rows"):
                lines += [" | ".join(cell.text.strip() for cell in row.cells) for row in block.rows]
            elif block.style.name.startswith(("Heading", "Title")) and block.text.strip():
                lines.append(f"# {block.text.strip()}")
            else:
                lines.append(block.text)
        doc.segments, doc.headings = _split_headings(lines, "s")
    elif doc.type == "csv":
        reader = csv.DictReader(io.StringIO(_read_text(path), newline=""))
        doc.columns = [c for c in reader.fieldnames or [] if c]
        doc.records = [{c: (row.get(c) or "").strip() for c in doc.columns} for row in reader]
        doc.rows = len(doc.records)
    else:
        doc.segments, doc.headings = _split_headings(_read_text(path).splitlines(), "s")
    if not doc.segments and not doc.records:
        doc.read, doc.note = False, "empty file"


def scan(folder: Path) -> list[Doc]:
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"document folder not found: {folder}")
    docs = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        kind = SUPPORTED.get(path.suffix.lower(), path.suffix.lstrip(".").lower() or "unknown")
        doc = Doc(name=path.relative_to(folder).as_posix(), type=kind,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if path.suffix.lower() not in SUPPORTED:
            doc.read, doc.note = False, "unsupported file type"
        else:
            try:
                _load(path, doc)
            except Exception as e:  # a corrupt file must not sink the run; it is reported
                doc.read, doc.note = False, f"could not be read: {type(e).__name__}: {e}"
        docs.append(doc)
    return docs


def _spread(headings: list[str], limit: int = 40) -> list[str]:
    """Headings from the whole document, not only its first pages."""
    unique = list(dict.fromkeys(headings))
    return unique[:: max(1, -(-len(unique) // limit))]


def summary(docs: list[Doc]) -> list[dict]:
    """The inventory as prompts see it."""
    return [{"name": d.name, "type": d.type, "pages": d.pages, "rows": d.rows,
             "headings": _spread(d.headings), "columns": d.columns,
             # a model that sees no values invents them ("part P12345")
             **({"sample_rows": [d.records[i] for i in sorted({0, len(d.records) // 2, len(d.records) - 1})]}
                if d.records else {})} for d in docs if d.read]


def row_text(record: dict) -> str:
    return "; ".join(f"{k}: {v}" for k, v in record.items())
