"""Filter, select and sort rows of a CSV already loaded from the docs folder. No free-form code, no paths."""

from ..inventory import row_text
from ..schemas import Chunk

MAX_ROWS = 20


def _number(value) -> float:
    return float(str(value).replace(",", "").strip())


def _matches(cell: str, op: str, value) -> bool:
    value = str(value)
    if op == "contains":
        return value.lower() in cell.lower()
    if op == "eq":
        try:
            return _number(cell) == _number(value)
        except ValueError:
            return cell.strip().lower() == value.strip().lower()
    compare = {"gt": float.__gt__, "ge": float.__ge__, "lt": float.__lt__, "le": float.__le__}[op]
    try:
        return compare(_number(cell), _number(value))
    except ValueError:
        return False


def run(docs: list, file: str, filters: list | None = None, select: list | None = None,
        sort_by: str | None = None, descending: bool = False, limit: int = 10):
    tables = {d.name: d for d in docs if d.type == "csv" and d.read}
    if file not in tables:
        raise ValueError(f"no such CSV. Available: {', '.join(tables) or 'none'}")
    table = tables[file]
    used = [f.get("column") for f in filters or []] + (select or []) + ([sort_by] if sort_by else [])
    unknown = [c for c in used if c not in table.columns]
    if unknown:
        raise ValueError(f"unknown column {unknown[0]!r}. Columns: {', '.join(table.columns)}")
    rows = list(enumerate(table.records, 1))
    for f in filters or []:
        op = f.get("op", "eq")
        if op not in ("eq", "contains", "gt", "ge", "lt", "le"):
            raise ValueError(f"unknown op {op!r}")
        rows = [(n, r) for n, r in rows if _matches(r[f["column"]], op, f.get("value", ""))]
    if sort_by:
        def key(item):
            try:
                return (0, _number(item[1][sort_by]), "")
            except ValueError:
                return (1, 0.0, item[1][sort_by].lower())

        rows.sort(key=key, reverse=bool(descending))
    total = len(rows)
    rows = rows[: max(1, min(int(limit), MAX_ROWS))]
    chunks = [Chunk(chunk_id=f"{file}#row{n}", doc=file,
                    text=row_text({c: r[c] for c in select or table.columns})) for n, r in rows]
    body = "\n".join(f"[{c.chunk_id}] {c.text}" for c in chunks)
    return f"{total} matching rows, showing {len(chunks)}\n{body}", chunks
