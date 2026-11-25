"""today, add_days, days_between."""

import datetime as dt


def run(op: str, date: str | None = None, days: int | None = None,
        start: str | None = None, end: str | None = None) -> str:
    parse = dt.date.fromisoformat
    if op == "today":
        return f"today is {dt.date.today().isoformat()}"
    if op == "add_days":
        base = parse(date) if date else dt.date.today()
        return f"{base.isoformat()} plus {int(days)} days is {(base + dt.timedelta(days=int(days))).isoformat()}"
    if op == "days_between":
        first = parse(start) if start else dt.date.today()
        return f"from {first.isoformat()} to {parse(end).isoformat()} is {(parse(end) - first).days} days"
    raise ValueError("op must be today, add_days or days_between")
