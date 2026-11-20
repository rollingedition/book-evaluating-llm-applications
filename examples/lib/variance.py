"""Per-item verdict counts over the variance set: how many of each item's samples the judge passed, read from a judge recording.

A reply with no readable verdict is never counted as FAIL. Its sample number is listed as unreadable, and an item with
any unreadable sample is left out of the flip rate and of the flagged items by the examples that use this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from statistics import NormalDist
from typing import Mapping, Sequence

import numpy as np

from lib.contract import parse_verdict
from lib.prompts import REF_SHA256
from lib.replay import ReplayModel

VARIANCE_SAMPLES = (1, 2, 3, 4, 5)  # the five samples of each item in the variance set; sample numbers start at 1
ALPHA = 0.05  # two-sided: 95% confidence
POWER = 0.80
_Z_ALPHA = NormalDist().inv_cdf(1 - ALPHA / 2)  # 1.96
_Z_SUM = _Z_ALPHA + NormalDist().inv_cdf(POWER)  # z_alpha + z_beta, 2.80


@dataclass(frozen=True, order=True)
class ItemVerdicts:
    """One item's verdicts over its samples: the PASS count among the readable ones, and the unreadable sample numbers."""

    item_id: str
    passes: int
    readable: int
    unreadable: tuple[int, ...]

    @property
    def complete(self) -> bool:
        """True when every sample has a readable verdict."""
        return not self.unreadable

    @property
    def flaky(self) -> bool:
        """True when the verdict differs across the samples: all readable, with some PASS and some FAIL."""
        return self.complete and 0 < self.passes < self.readable


def summarize(replies: Mapping[str, Mapping[int, str]]) -> list[ItemVerdicts]:
    """The per-item counts from raw judge replies keyed by item id, then by sample number. Sorted by item id."""
    summaries = []
    for item_id in sorted(replies):
        by_sample = replies[item_id]
        verdicts = {sample: parse_verdict(by_sample[sample]) for sample in sorted(by_sample)}
        unreadable = tuple(sample for sample, verdict in verdicts.items() if verdict is None)
        readable = [verdict for verdict in verdicts.values() if verdict is not None]
        passes = sum(1 for verdict in readable if verdict == "PASS")
        summaries.append(ItemVerdicts(item_id, passes, len(readable), unreadable))
    return summaries


def item_pass_counts(
    recording: str, item_ids: Sequence[str], samples: Sequence[int] = VARIANCE_SAMPLES
) -> list[ItemVerdicts]:
    """Each item's verdicts over the given samples, read from a judge recording made from the reference-guided prompt.

    A sample the recording does not hold raises KeyError, naming the recording and the key.
    """
    model = ReplayModel(recording, REF_SHA256)
    replies = {item_id: {sample: model.reply(item_id, sample) for sample in samples} for item_id in item_ids}
    return summarize(replies)


def paired_difference_variance(first, second) -> float:
    """The variance over the items of d = second - first, one paired difference per item, with d in {-1, 0, +1}.

    Equals p_discordant - mean(d)^2: the share of items on which the two runs disagree, less the squared mean.
    Each item counts once; the two arrays must hold the same items in the same order.
    """
    d = np.asarray(second, dtype=float) - np.asarray(first, dtype=float)
    if d.ndim != 1 or d.size == 0:
        raise ValueError("a paired difference variance needs two non-empty one-dimensional lists of the same items")
    return float(np.mean(d * d) - np.mean(d) ** 2)


def items_needed(var_d: float, delta_points: float) -> int:
    """n = (z_alpha + z_beta)^2 * var_d / delta^2, rounded up. delta is in points; var_d is the variance of d."""
    return ceil(_Z_SUM ** 2 * var_d / (delta_points / 100) ** 2)


def smallest_difference_points(var_d: float, n: int) -> float:
    """The smallest difference in points that n items detect: (z_alpha + z_beta) * sqrt(var_d / n)."""
    return 100 * _Z_SUM * (var_d / n) ** 0.5


def interval_width_points(var_d: float, n: int) -> float:
    """The width in points of the 95% interval of the mean difference over n items: 2 * z_alpha * sqrt(var_d / n)."""
    return 200 * _Z_ALPHA * (var_d / n) ** 0.5


def z_sum(alpha: float = ALPHA) -> float:
    """z_alpha + z_beta for a two-sided test at level alpha and POWER: 2.80 at alpha 0.05, 3.24 at alpha 0.05 / 3."""
    return NormalDist().inv_cdf(1 - alpha / 2) + NormalDist().inv_cdf(POWER)


def items_needed_at(var_d: float, delta_points: float, alpha: float = ALPHA) -> int:
    """n = z_sum(alpha)^2 * var_d / delta^2, rounded up, for a two-sided test at level alpha. delta is in points."""
    return ceil(z_sum(alpha) ** 2 * var_d / (delta_points / 100) ** 2)


def smallest_difference_at(var_d: float, n: int, alpha: float = ALPHA) -> float:
    """The smallest difference in points that n items detect at level alpha: z_sum(alpha) * sqrt(var_d / n)."""
    return 100 * z_sum(alpha) * (var_d / n) ** 0.5
