"""Helpers for the chapter 7 examples: reply length in words and its bands, verdicts read without raising, the position a
flipped pair leaned to, and an interval for the gap between two bands.

Nothing here prints. An unreadable verdict is None, never FAIL: the caller decides what to leave out, and says so.
"""
from __future__ import annotations

import bisect
from collections.abc import Mapping, Sequence

import numpy as np

from lib import SEED
from lib.contract import parse_reply, parse_verdict
from lib.judging import BothOrders
from lib.prompts import REF_SHA256
from lib.replay import ReplayModel
from lib.stats import RESAMPLES

LENGTH_EDGES = (15, 30)  # band edges in words: a reply of 15 words is in the middle band, one of 30 in the last
LENGTH_BANDS = ("under 15 words", "15 to 29 words", "30 words or more")  # one name per band, shortest first


def word_count(text: str) -> int:
    """The number of words in the text: runs of non-space characters, as a reader counts them."""
    return len(text.split())


def length_band(words: int) -> str:
    """The band of a reply of `words` words, from LENGTH_BANDS. A band includes its lower edge, so 15 is in the middle band."""
    if words < 0:
        raise ValueError("a word count cannot be negative")
    return LENGTH_BANDS[bisect.bisect_right(LENGTH_EDGES, words)]


def reply_lengths(recording: str, item_ids: Sequence[str]) -> dict[str, int]:
    """The word count of each answered reply (sample 0) in the recording, by item id, sorted. Declined replies are left out."""
    model = ReplayModel(recording)
    lengths: dict[str, int] = {}
    for item_id in sorted(item_ids):
        reply = parse_reply(model.reply(item_id, 0))
        if not reply.declined:
            lengths[item_id] = word_count(reply.text)
    return lengths


def read_verdicts(recording: str, item_ids: Sequence[str]) -> dict[str, str | None]:
    """The reference-guided verdict per item, 'PASS' or 'FAIL', or None when the reply has no readable verdict line.

    Sorted by item id. Unlike judging.verdicts, an unreadable line is returned as None instead of raised.
    """
    model = ReplayModel(recording, REF_SHA256)
    return {item_id: parse_verdict(model.reply(item_id, 0)) for item_id in sorted(item_ids)}


def band_outcomes(lengths: Mapping[str, int], verdicts: Mapping[str, str | None]) -> list[tuple[str, np.ndarray]]:
    """For each band in LENGTH_BANDS order, the 1.0 (PASS) and 0.0 (FAIL) outcomes of its readable items, sorted by id.

    An item needs a length and a readable verdict. An item whose verdict is None is left out, never counted as FAIL.
    """
    grouped: dict[str, list[float]] = {band: [] for band in LENGTH_BANDS}
    for item_id in sorted(lengths):
        if item_id not in verdicts:
            raise KeyError(f"no verdict for item {item_id!r}")
        verdict = verdicts[item_id]
        if verdict is not None:
            grouped[length_band(lengths[item_id])].append(1.0 if verdict == "PASS" else 0.0)
    return [(band, np.array(grouped[band], dtype=float)) for band in LENGTH_BANDS]


def gap_interval(low: np.ndarray, high: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    """The percentile bootstrap interval of mean(high) minus mean(low), resampling each group's items on its own.

    Each group is resampled RESAMPLES times from one generator made here from SEED, so the interval is the same on every call.
    """
    rng = np.random.default_rng(SEED)
    low_picks = rng.integers(0, low.size, size=(RESAMPLES, low.size))
    high_picks = rng.integers(0, high.size, size=(RESAMPLES, high.size))
    gaps = high[high_picks].mean(axis=1) - low[low_picks].mean(axis=1)
    tail = (1.0 - level) / 2.0
    lo, hi = np.quantile(gaps, [tail, 1.0 - tail])
    return float(lo), float(hi)


def unreadable_count(recordings: Sequence[str], item_ids: Sequence[str]) -> tuple[int, int]:
    """(unreadable, total): the verdicts with no readable line, and all verdicts, across every recording and item."""
    found = [read_verdicts(name, item_ids) for name in recordings]
    unreadable = sum(verdict is None for verdicts in found for verdict in verdicts.values())
    return unreadable, sum(len(verdicts) for verdicts in found)


def same_model_count(judge_recordings: Sequence[str]) -> tuple[int, int]:
    """(same, total): how many judge recordings were made by the same model as the assistant recording they judged."""
    same = 0
    for name in judge_recordings:
        judge = ReplayModel(name).manifest
        assistant = ReplayModel(judge["judges"]["recording"]).manifest
        same += judge["model"] == assistant["model"]
    return same, len(judge_recordings)


def paired_passes(first: str, second: str, item_ids: Sequence[str]) -> tuple[list[str], np.ndarray, np.ndarray]:
    """The items readable in both recordings (sorted), and each one's PASS as 1.0 or 0.0 under the first and the second."""
    a = read_verdicts(first, item_ids)
    b = read_verdicts(second, item_ids)
    both = [item_id for item_id in sorted(item_ids) if a[item_id] is not None and b[item_id] is not None]
    return (
        both,
        np.array([a[item_id] == "PASS" for item_id in both], dtype=float),
        np.array([b[item_id] == "PASS" for item_id in both], dtype=float),
    )


def flip_direction(pair: BothOrders) -> str | None:
    """For a flipped pair, the position whose letter won in both orders: 'first' (A) or 'second' (B). None for other kinds.

    In order ab a mapped 'a' is letter A; in order ba the same letter A maps to 'b'. So ab 'a' with ba 'b' is A both times.
    """
    if pair.kind != "flipped":
        return None
    return "first" if pair.ab == "a" else "second"
