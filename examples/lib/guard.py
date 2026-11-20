"""The decline guard of chapter 10: a rule on recorded replies and their retrieval scores, threshold chosen on dev.

The guard reads the `unfiltered` recording, whose replies were made from every version's sections, so its score is the
top BM25 score over the all-version index. A reply becomes a decline when that score is below the threshold; otherwise
the recorded reply stands. Retrieval is deterministic, so no model runs again. `contexts_match` checks that the index
reproduces the sections the recording was made from.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache

from lib.contract import parse_reply
from lib.docs import load_sections
from lib.prompts import P1_SHA256
from lib.replay import RECORDED, ReplayModel
from lib.retrieval import Retriever
from lib.testset import Item, load_items

GUARD_RECORDING = "assistant-unfiltered"
GRID = tuple(step * 0.25 for step in range(41))  # 0.00 to 10.00 in steps of 0.25, above every top score in the set
RULE = (
    "pick the threshold in GRID whose false refusal rate plus false answer rate is smallest, each rate over its own "
    "denominator; when two thresholds tie, take the lower one"
)


@dataclass(frozen=True)
class Row:
    """One answerable or unanswerable item: its kind, its top score over every version, and the recorded decline."""

    item_id: str
    kind: str
    score: float
    declined: bool


@lru_cache(maxsize=1)
def _all_versions_retriever() -> Retriever:
    """BM25 over the sections of every version, built once."""
    return Retriever(load_sections())


def top_score(item: Item) -> float:
    """The top BM25 score for the item's question over every version's sections."""
    return _all_versions_retriever().retrieve(item.question, 1)[0].score


def contexts_match(split: str) -> int:
    """How many items of the split have a recorded context that differs from the top three retrieved. Zero means
    retrieval reproduces the recording."""
    wanted = {item.id: item for item in load_items(split=split)}
    mismatches = 0
    for line in (RECORDED / GUARD_RECORDING / "replies.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["item"] not in wanted:
            continue
        hits = _all_versions_retriever().retrieve(wanted[row["item"]].question, 3)
        if [f"{hit.version}/{hit.section_id}" for hit in hits] != row["context"]:
            mismatches += 1
    return mismatches


def rows(split: str) -> list[Row]:
    """The answerable and unanswerable items of one split, sorted by id, with the recorded decline of each."""
    model = ReplayModel(GUARD_RECORDING, P1_SHA256)
    found = []
    for item in load_items(split=split):
        if item.kind not in ("answerable", "unanswerable"):  # version-dependent and ambiguous are not in either rate
            continue
        declined = parse_reply(model.reply(item.id, 0)).declined
        found.append(Row(item.id, item.kind, top_score(item), declined))
    return sorted(found, key=lambda row: row.item_id)


def guarded(row: Row, threshold: float) -> bool:
    """Whether the reply is a decline after the guard: the recorded decline, or a top score below the threshold."""
    return row.declined or row.score < threshold


def denominators(rows_: list[Row]) -> tuple[int, int]:
    """The number of answerable items and of unanswerable items: the denominators of the two rates."""
    return sum(row.kind == "answerable" for row in rows_), sum(row.kind == "unanswerable" for row in rows_)


def errors(rows_: list[Row], threshold: float) -> tuple[list[str], list[str]]:
    """The false refusals (answerable items declined) and false answers (unanswerable items answered), by id."""
    refusals = [row.item_id for row in rows_ if row.kind == "answerable" and guarded(row, threshold)]
    answers = [row.item_id for row in rows_ if row.kind == "unanswerable" and not guarded(row, threshold)]
    return refusals, answers


def pick_threshold(rows_: list[Row]) -> float:
    """The dev rule (RULE): the threshold in GRID with the smallest false refusal rate plus false answer rate."""
    answerable, unanswerable = denominators(rows_)
    best, best_total = None, None
    for threshold in GRID:
        refusals, answers = errors(rows_, threshold)
        total = Fraction(len(refusals), answerable) + Fraction(len(answers), unanswerable)  # exact, so ties are real
        if best_total is None or total < best_total:  # strict: an equal total keeps the lower threshold
            best, best_total = threshold, total
    return best
