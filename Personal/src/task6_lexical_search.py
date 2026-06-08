"""Task 6 - Lexical Search Module (BM25)."""

from __future__ import annotations

import math
from functools import lru_cache

from .retrieval_utils import load_corpus, tokenize


CORPUS: list[dict] = load_corpus()


class SimpleBM25:
    """Small BM25 implementation used when rank-bm25 is unavailable."""

    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.tokenized_corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_len = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0.0
        self.df: dict[str, int] = {}
        self.term_freqs: list[dict[str, int]] = []

        for doc in tokenized_corpus:
            freqs: dict[str, int] = {}
            for token in doc:
                freqs[token] = freqs.get(token, 0) + 1
            self.term_freqs.append(freqs)
            for token in freqs:
                self.df[token] = self.df.get(token, 0) + 1

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        n_docs = len(self.tokenized_corpus)
        if n_docs == 0:
            return []

        scores: list[float] = []
        for idx, freqs in enumerate(self.term_freqs):
            score = 0.0
            doc_len = self.doc_len[idx] or 1
            for token in query_tokens:
                tf = freqs.get(token, 0)
                if tf == 0:
                    continue
                idf = math.log(1 + (n_docs - self.df.get(token, 0) + 0.5) / (self.df.get(token, 0) + 0.5))
                denom = tf + self.k1 * (1 - self.b + self.b * doc_len / (self.avgdl or 1))
                score += idf * (tf * (self.k1 + 1)) / denom
            scores.append(score)
        return scores


def build_bm25_index(corpus: list[dict]):
    """Build BM25 index from a corpus of {'content', 'metadata'} dictionaries."""
    tokenized_corpus = [tokenize(doc["content"]) for doc in corpus]
    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized_corpus)
    except Exception:
        return SimpleBM25(tokenized_corpus)


def _build_cached_index():
    tokenized_corpus = [tokenize(doc["content"]) for doc in CORPUS]
    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized_corpus)
    except Exception:
        return SimpleBM25(tokenized_corpus)


@lru_cache(maxsize=1)
def _bm25_index():
    return _build_cached_index()


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Search with BM25 and return results sorted by descending score."""
    if not query.strip() or top_k <= 0 or not CORPUS:
        return []

    scores = _bm25_index().get_scores(tokenize(query))
    ranked = sorted(enumerate(scores), key=lambda pair: float(pair[1]), reverse=True)

    results: list[dict] = []
    for idx, score in ranked[:top_k]:
        if float(score) <= 0:
            continue
        results.append(
            {
                "content": CORPUS[idx]["content"],
                "score": float(score),
                "metadata": CORPUS[idx].get("metadata", {}),
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("Dieu 248 ma tuy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
