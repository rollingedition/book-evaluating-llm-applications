"""A gate over a paired difference: candidate minus baseline, per item, with the seeded percentile bootstrap from lib.stats.

The gate fails only when the upper bound of the difference's interval is below minus the threshold, so the drop is larger
than the threshold at the interval's level. A drop whose interval still reaches above minus the threshold passes: the gate
found no drop larger than the threshold. That is not a claim that the candidate is as good as the baseline.

Several metrics checked in one gate use the adjusted level of plan section 6.3: with `comparisons` = m the interval is at
1 - 0.05 / m.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from lib.stats import bootstrap_mean

FAIL = "fail"
PASS = "pass"


@dataclass(frozen=True)
class Gate:
    """The decision and the paired difference it rests on. Rates are proportions; the threshold is in points."""

    decision: str  # FAIL or PASS
    n: int  # paired items
    difference: float  # candidate minus baseline, as a proportion (-0.05 is a drop of five points)
    lo: float  # lower bound of the interval, as a proportion
    hi: float  # upper bound of the interval, as a proportion
    threshold_points: float  # the drop the gate must be sure of, in points
    level: float  # the interval's level, 0.95 for one comparison


def gate(baseline, candidate, threshold_points: float, comparisons: int = 1) -> Gate:
    """Decide on the paired difference of two runs over the same items, one 0 or 1 per item in the same order."""
    base = np.asarray(baseline, dtype=float)
    cand = np.asarray(candidate, dtype=float)
    if base.ndim != 1 or base.shape != cand.shape or base.size == 0:
        raise ValueError("a gate needs two non-empty lists of per-item values of the same length")
    if not np.all(np.isin(base, (0.0, 1.0))) or not np.all(np.isin(cand, (0.0, 1.0))):
        raise ValueError("a gate reads pass (1) or fail (0) per item")
    if threshold_points <= 0:
        raise ValueError("a gate threshold is a drop in points, above 0")
    if comparisons < 1:
        raise ValueError("a gate checks at least one comparison")
    level = 1.0 - 0.05 / comparisons  # plan section 6.3: Bonferroni over the m metrics the gate checks
    diff = cand - base  # candidate minus baseline: a drop is negative
    lo, hi = bootstrap_mean(diff, level=level)  # the one seeded generator, SEED, as in lib.stats
    decision = FAIL if hi < -threshold_points / 100.0 else PASS
    return Gate(
        decision=decision,
        n=int(base.size),
        difference=float(np.mean(diff)),
        lo=lo,
        hi=hi,
        threshold_points=threshold_points,
        level=level,
    )
