"""The reference-guided judge's verdicts from a recording, and paired comparisons of two runs over the same items.

A verdict is read with lib.contract.parse_verdict. A reply with no readable verdict line is an error here, never a
FAIL: a judge that did not answer has not judged the item.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Sequence

import numpy as np

from lib.prompts import PAIR_SHA256, REF_SHA256
from lib.contract import parse_verdict
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean

# The pairwise verdict on the reply's first line: A, B or TIE. TIE is read so that a judge which writes it is counted as a
# tie and not refused; the pairwise rubric itself asks for A or B only.
PAIR_VERDICT = re.compile(r"^VERDICT:\s*(A|B|TIE)$")
PAIRS = Path(__file__).resolve().parent.parent / "data" / "helpsteer2" / "preferences.jsonl"
KINDS = ("consistent", "flipped", "tie", "unreadable")


def verdicts(recording: str, item_ids: Sequence[str]) -> dict[str, str]:
    """The judge's verdict (PASS or FAIL) per item id, from the recording, keyed in sorted id order."""
    model = ReplayModel(recording, REF_SHA256)
    found: dict[str, str] = {}
    for item_id in sorted(item_ids):
        verdict = parse_verdict(model.reply(item_id, 0))
        if verdict is None:
            raise ValueError(f"judge recording {recording!r} has no readable verdict for item {item_id!r}")
        found[item_id] = verdict
    return found


def passed(found: dict[str, str]) -> np.ndarray:
    """1.0 for each PASS and 0.0 for each FAIL, in the dict's (sorted) key order."""
    return np.array([1.0 if found[item_id] == "PASS" else 0.0 for item_id in found], dtype=float)


@dataclass(frozen=True)
class Paired:
    """Two runs over the same n items: each pass rate, the paired difference (second minus first), its interval."""
    n: int
    first: np.ndarray
    second: np.ndarray
    diff_lo: float
    diff_hi: float

    @property
    def difference(self) -> float:
        """The mean of the paired differences, as a proportion (0.05 is five percentage points)."""
        return float(np.mean(self.second - self.first))


def paired(first_recording: str, second_recording: str, item_ids: Sequence[str], level: float = 0.95) -> Paired:
    """Pass each item under both runs, then the paired difference with its bootstrap interval over items."""
    ordered = sorted(item_ids)
    first = passed(verdicts(first_recording, ordered))
    second = passed(verdicts(second_recording, ordered))
    lo, hi = bootstrap_mean(second - first, level=level)
    return Paired(n=len(ordered), first=first, second=second, diff_lo=lo, diff_hi=hi)


def parse_pair_verdict(raw: str) -> str | None:
    """'A', 'B' or 'TIE' from the reply's first non-empty line, else None. Markdown emphasis around it is ignored."""
    lines = [line.strip().strip("*`").strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None
    match = PAIR_VERDICT.match(lines[0])
    return match.group(1) if match else None


SUPPORT_VERDICT = re.compile(r"^VERDICT:\s*(SUPPORTED|UNSUPPORTED)$")


def parse_support_verdict(raw: str) -> str | None:
    """'SUPPORTED' or 'UNSUPPORTED' from the reply's first non-empty line, else None. Markdown emphasis around it is ignored."""
    lines = [line.strip().strip("*`").strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None
    match = SUPPORT_VERDICT.match(lines[0])
    return match.group(1) if match else None


class Pair(NamedTuple):
    """A human preference pair's split ('dev' or 'held-out') and the response the human preferred ('a' or 'b')."""
    split: str
    preferred: str


def human_pairs(split: str | None = None) -> dict[str, Pair]:
    """The HelpSteer2 preference pairs by id, in sorted id order, from the data file; one split when one is named."""
    rows = [json.loads(line) for line in PAIRS.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {
        row["id"]: Pair(row["split"], row["preferred"])
        for row in sorted(rows, key=lambda r: r["id"])
        if split is None or row["split"] == split
    }


def original(letter: str | None, order: str) -> str | None:
    """The original response a verdict picks: 'a', 'b', 'tie', or None when there is no verdict.

    In order ab, A is response_a. In order ba the two responses are swapped, so A is response_b.
    """
    if letter is None:
        return None
    if letter == "TIE":
        return "tie"
    a_wins_letter = letter == "A"
    if order == "ab":
        return "a" if a_wins_letter else "b"
    return "b" if a_wins_letter else "a"


def classify(ab: str | None, ba: str | None) -> str:
    """The kind of one pair from its two mapped verdicts, from KINDS.

    unreadable: a verdict is missing in either order. tie: a TIE in either order. consistent: the same original response
    wins in both orders. flipped: the same letter wins in both orders, so the verdict followed the position.
    """
    if ab is None or ba is None:
        return "unreadable"
    if "tie" in (ab, ba):
        return "tie"
    return "consistent" if ab == ba else "flipped"


@dataclass(frozen=True, order=True)
class BothOrders:
    """One pair judged in both orders: the original response picked in order ab and in order ba, and the kind."""
    pair_id: str
    ab: str | None
    ba: str | None
    kind: str


def both_orders(ab_recording: str, ba_recording: str, pair_ids: Sequence[str]) -> list[BothOrders]:
    """Each pair's verdict in both orders, mapped back to the original responses, sorted by pair id.

    Both recordings must be made from PAIR_SHA256 and must say their own order in the manifest, so they cannot be swapped.
    """
    ab = ReplayModel(ab_recording, PAIR_SHA256)
    ba = ReplayModel(ba_recording, PAIR_SHA256)
    for model, order in ((ab, "ab"), (ba, "ba")):
        if model.manifest["order"] != order:
            raise ValueError(f"recording {model.name!r} is order {model.manifest['order']!r}, not {order!r}")
    found = []
    for pair_id in sorted(pair_ids):
        first = original(parse_pair_verdict(ab.reply(pair_id, 0)), "ab")
        second = original(parse_pair_verdict(ba.reply(pair_id, 0)), "ba")
        found.append(BothOrders(pair_id, first, second, classify(first, second)))
    return found
