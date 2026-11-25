"""Chunking and retrieval: BM25 + MiniLM, fused with weighted reciprocal rank fusion."""

import math
import re
import threading
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import numpy as np

from .inventory import Doc, row_text
from .schemas import Chunk, Retrieval

TOKEN = re.compile(r"[a-z0-9]+(?:[-./_][a-z0-9]+)*")
RRF_K = 60
CODE = re.compile(r"(?=.*\d)(?=.*[a-z]).*[-./_]")
RARE = 3  # a code in this few chunks names them


def tokenize(text: str) -> list[str]:
    tokens = []
    for token in TOKEN.findall(text.lower()):
        tokens.append(token)
        parts = re.split(r"[-./_]", token)
        if len(parts) > 1:  # keep the whole part code and also its pieces
            tokens += parts
    return tokens


class Embedder:
    def __init__(self, model: str):
        self.model_name = model
        self._model = None
        self._lock = threading.Lock()

    def __call__(self, texts: list[str]) -> np.ndarray:
        with self._lock:
            if self._model is None:
                from fastembed import TextEmbedding

                self._model = TextEmbedding(self.model_name)
            vectors = np.array(list(self._model.embed(texts)), dtype=np.float32)
        return vectors / np.clip(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9, None)


def _pack(text: str, size: int, overlap: int) -> list[str]:
    """Pack lines into chunks of about `size` tokens (1 token is about 0.75 words)."""
    max_words, keep = max(size * 3 // 4, 20), overlap * 3 // 4
    chunks, words, fresh = [], 0, 0
    current: list[str] = []
    for line in filter(None, (ln.strip() for ln in text.splitlines())):
        tokens = line.split()
        for i in range(0, len(tokens), max_words):
            piece = tokens[i : i + max_words]
            if fresh and words + len(piece) > max_words:
                chunks.append(" ".join(current))
                tail = chunks[-1].split()[-keep:] if keep else []
                current, words, fresh = [" ".join(tail)] if tail else [], len(tail), 0
            current.append(" ".join(piece))
            words += len(piece)
            fresh += len(piece)
    if fresh:
        chunks.append(" ".join(current))
    return chunks


def chunk_docs(docs: list[Doc], size: int, overlap: int) -> list[Chunk]:
    readable = [d for d in docs if d.read]
    stems = Counter(str(PurePosixPath(d.name).with_suffix("")) for d in readable)
    chunks = []
    for doc in readable:
        if doc.type == "csv":  # one chunk per row
            chunks += [Chunk(chunk_id=f"{doc.name}#row{n}", doc=doc.name, text=row_text(r))
                       for n, r in enumerate(doc.records, 1)]
            continue
        stem = str(PurePosixPath(doc.name).with_suffix(""))
        stem = stem if stems[stem] == 1 else doc.name
        for segment in doc.segments:
            chunks += [Chunk(chunk_id=f"{stem}#{segment.section}#c{n}", doc=doc.name, text=text)
                       for n, text in enumerate(_pack(segment.text, size, overlap), 1)]
    return chunks


class _Built:
    def __init__(self, chunks: list[Chunk], embed):
        self.chunks = chunks
        self.vectors = embed([c.text for c in chunks]) if chunks else np.zeros((0, 1), np.float32)
        self.postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self.lengths = []
        for i, chunk in enumerate(chunks):
            counts = Counter(tokenize(chunk.text))
            self.lengths.append(sum(counts.values()))
            for term, n in counts.items():
                self.postings[term].append((i, n))
        self.average = sum(self.lengths) / len(self.lengths) if self.lengths else 1

    def bm25(self, query: str, k1: float = 1.5, b: float = 0.75) -> np.ndarray:
        scores = np.zeros(len(self.chunks))
        for term in set(tokenize(query)):
            hits = self.postings.get(term, [])
            idf = math.log(1 + (len(self.chunks) - len(hits) + 0.5) / (len(hits) + 0.5))
            for i, n in hits:
                scores[i] += idf * n * (k1 + 1) / (n + k1 * (1 - b + b * self.lengths[i] / self.average))
        return scores


class Index:
    # Note: indexes live in memory and are rebuilt per process; persist them if a folder takes minutes to embed.
    def __init__(self, docs: list[Doc], embed, folder: Path | None = None):
        self.docs = docs
        self.embed = embed
        self.folder = folder
        self._built: dict[tuple[int, int], _Built] = {}
        self._lock = threading.Lock()

    def _get(self, params: Retrieval) -> _Built:
        key = (params.chunk_size, params.chunk_overlap)
        with self._lock:
            if key not in self._built:
                self._built[key] = _Built(chunk_docs(self.docs, *key), self.embed)
            return self._built[key]

    def chunks(self, params: Retrieval = Retrieval()) -> list[Chunk]:
        return self._get(params).chunks

    def ranking(self, query: str, params: Retrieval = Retrieval()) -> list[tuple[Chunk, float]]:
        """Every chunk, best first, with its cosine similarity to the query."""
        built = self._get(params)
        if not built.chunks:
            return []
        cosine = built.vectors @ self.embed([query])[0]
        keyword = built.bm25(query)
        n = len(built.chunks)
        dense_rank, keyword_rank = np.empty(n), np.empty(n)
        dense_rank[np.argsort(-cosine, kind="stable")] = np.arange(1, n + 1)
        keyword_rank[np.argsort(-keyword, kind="stable")] = np.arange(1, n + 1)
        keyword_score = np.where(keyword > 0, 1 / (RRF_K + keyword_rank), 0)  # no shared word, no keyword credit
        fused = params.bm25_weight * keyword_score + (1 - params.bm25_weight) / (RRF_K + dense_rank)
        for term in set(tokenize(query)):
            hits = built.postings.get(term, [])
            if len(hits) <= RARE and CODE.match(term):  # near-identical rows must not bury the part that was asked for
                for i, _ in hits:
                    fused[i] += 1
        return [(built.chunks[i], float(cosine[i])) for i in np.argsort(-fused, kind="stable")]

    def search(self, query: str, params: Retrieval = Retrieval(), k: int | None = None) -> list[Chunk]:
        """Top k chunks that pass the min_score gate (a cosine floor)."""
        top = self.ranking(query, params)[: k or params.top_k]
        return [chunk for chunk, score in top if score >= params.min_score]
