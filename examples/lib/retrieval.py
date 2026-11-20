"""BM25 retrieval over doc sections, with bm25s at its defaults (k1=1.5, b=0.75) and English stopwords.

One index per version, and one over every version for the `unfiltered` variant. Scores come from
`BM25.get_scores`, not from `retrieve`, because bm25s returns tied documents in an order that is not index order
(plan section 11, probe 3). Hits are sorted here by (-score, section_id, version), so a tie always breaks the same way.
A query with no matching word still returns k hits, all with score 0, in that order.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import bm25s

from lib.docs import Section


@dataclass(frozen=True)
class Hit:
    """One retrieved section: its version, ID and BM25 score."""

    version: str
    section_id: str
    score: float


class Retriever:
    """A BM25 index over one fixed list of sections."""

    def __init__(self, sections: Sequence[Section]) -> None:
        if not sections:
            raise ValueError("a retriever needs at least one section")
        self._keys = [(s.version, s.section_id) for s in sections]
        corpus = [f"{s.title}\n{s.text}" for s in sections]
        self._bm25 = bm25s.BM25()
        self._bm25.index(bm25s.tokenize(corpus, stopwords="en", return_ids=True, show_progress=False),
                         show_progress=False)

    def retrieve(self, query: str, k: int) -> list[Hit]:
        """The top k sections for the query, sorted by (-score, section_id, version)."""
        tokens = bm25s.tokenize([query], stopwords="en", return_ids=False, show_progress=False)[0]
        scores = self._bm25.get_scores(tokens) if tokens else [0.0] * len(self._keys)
        hits = [Hit(version, sid, float(score)) for (version, sid), score in zip(self._keys, scores)]
        hits.sort(key=lambda h: (-h.score, h.section_id, h.version))
        return hits[:k]
