"""Group split by source chunk: every case built from one paragraph lands on the same side."""

import random
from collections import Counter

from .schemas import Case


def groups(cases: list[Case]) -> list[list[Case]]:
    """Connected components of cases that share a source chunk."""
    parent = list(range(len(cases)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict[str, int] = {}
    for i, case in enumerate(cases):
        for chunk in case.source_chunks:
            parent[find(i)] = find(owner.setdefault(chunk.chunk_id, i))
    found: dict[int, list[Case]] = {}
    for i, case in enumerate(cases):
        found.setdefault(find(i), []).append(case)
    return list(found.values())


def unlink(cases: list[Case]) -> tuple[list[Case], list[Case]]:
    """A small folder can chain every case into one group, leaving nothing to seal.

    Drop multi-chunk cases, latest first, until no group holds more than two thirds. Return (kept, dropped).
    """
    kept, dropped = list(cases), []
    while kept and max(map(len, groups(kept))) * 3 > len(kept) * 2:
        link = next((c for c in reversed(kept) if len(c.source_chunks) > 1), None)
        if link is None:
            break
        kept.remove(link)
        dropped.append(link)
    return kept, dropped


def split(cases: list[Case], seed: int = 7) -> tuple[list[Case], list[Case], dict]:
    """About 2/3 train and 1/3 sealed, stratified by category. Renames cases T.. and S.."""
    shuffled = groups(cases)
    random.Random(seed).shuffle(shuffled)
    shuffled.sort(key=lambda g: -len({c.category for c in g}))  # mixed groups first, while there is room
    wanted = {c: round(n / 3) for c, n in Counter(x.category for x in cases).items()}

    def distance(counts):
        return sum((counts[c] - n) ** 2 for c, n in wanted.items())

    train, sealed, held = [], [], Counter()
    for group in shuffled:
        counts = Counter(c.category for c in group)
        if distance(held + counts) < distance(held):  # seal it if that moves every category toward its third
            sealed += group
            held += counts
        else:
            train += group
    if not sealed and len(shuffled) > 1:
        smallest = min(shuffled, key=len)
        sealed, train = smallest, [c for c in train if c not in smallest]
    record = {"seed": seed, "train": {}, "sealed": {}}
    for name, prefix, side in (("train", "T", train), ("sealed", "S", sealed)):
        for n, case in enumerate(side, 1):
            record[name][f"{prefix}{n:02d}"] = case.id
            case.id = f"{prefix}{n:02d}"
    return train, sealed, record
