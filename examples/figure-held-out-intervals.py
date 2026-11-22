"""Draws each variant's paired difference from the baseline on the held-out items, with the 98.33% interval held-out-variants
reports and the 95% interval from the same resamples. The printed lines repeat held-out-variants' figures; the asserts
check that these are the resamples its bootstrap draws, and that each 98.33% interval is wider than its 95% one."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import numpy as np

from lib import SEED
from lib.calibration import readable_verdicts
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import RESAMPLES, bootstrap_mean, interval_points
from lib.testset import load_items

BASELINE = "baseline"
VARIANTS = ("prompt-b", "k5", "unfiltered")
LEVEL = 1 - 0.05 / len(VARIANTS)  # the level held-out-variants uses: 98.33% for m = 3
items = [item.id for item in load_items(split="held-out")]
base_found, base_unreadable = readable_verdicts(f"judge-answers-{BASELINE}", items, REF_SHA256)
rows = []
for name in VARIANTS:
    found, unreadable = readable_verdicts(f"judge-answers-{name}", items, REF_SHA256)
    kept = [i for i in items if i not in {x for x, _ in base_unreadable + unreadable}]  # dropped from both sides, as there
    diff = passed({i: found[i] for i in kept}) - passed({i: base_found[i] for i in kept})  # variant minus baseline
    lo, hi = bootstrap_mean(diff, level=LEVEL)
    # bootstrap_mean keeps only the 98.33% ends: this redraws its resamples, with the same generator, seed and draw order.
    means = diff[np.random.default_rng(SEED).integers(0, diff.size, size=(RESAMPLES, diff.size))].mean(axis=1)
    assert np.allclose(np.quantile(means, [(1 - LEVEL) / 2, 1 - (1 - LEVEL) / 2]), [lo, hi]), "resamples must give the interval"
    lo95, hi95 = np.quantile(means, [0.025, 0.975])  # the same resamples, at the usual 95% level
    assert hi - lo > hi95 - lo95, "the 98.33% interval must be wider than the 95% one"
    rows.append((diff, lo, hi, lo95, hi95))
    print(f"{name} minus baseline, difference: {100 * float(diff.mean()):+.1f} points")
    print(f"{name} minus baseline, {100 * LEVEL:.2f}% interval: {interval_points(lo, hi)}")
    print(f"{name} minus baseline, 95% interval: {interval_points(lo95, hi95)}")
    print(f"{name} minus baseline, reading at {100 * LEVEL:.2f}%: {'better' if lo > 0 else 'worse' if hi < 0 else 'no difference detected'}")
    print(f"{name} minus baseline, reading at 95%: {'better' if lo95 > 0 else 'worse' if hi95 < 0 else 'no difference detected'}")

fig, ax = new_figure(height=2.8)
ys = np.arange(len(VARIANTS))[::-1]  # the first variant on top
ax.hlines(ys, [100 * r[1] for r in rows], [100 * r[2] for r in rows], color=ACCENT, linewidth=6, label=f"{100 * LEVEL:.2f}% interval (held-out level)")
ax.hlines(ys, [100 * r[3] for r in rows], [100 * r[4] for r in rows], color=INK, linewidth=1.2, label="95% interval, same resamples")
ax.scatter([100 * r[0].mean() for r in rows], ys, color=INK, s=18, zorder=3, label="point difference")
ax.axvline(0, color=MUTED, linewidth=1.0, label="zero: no difference")  # solid: the claim each interval is read against
ax.set_yticks(ys, ["prompt B", "k5", "unfiltered"])
ax.set_xlabel("variant minus baseline, in percentage points")
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2)  # above the plot, clear of the intervals
save(fig, "held-out-intervals")
