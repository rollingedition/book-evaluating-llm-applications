"""Draws the dev false refusal rate and false answer rate against the guard's threshold, with their sum dashed and the
rule's pick marked. The printed lines are the pick, its two rates and the lowest sum; the asserts check that the rates
are the lines tune-guard-dev prints, and that the pick has the lowest sum on the grid."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from fractions import Fraction

from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.guard import GRID, denominators, errors, pick_threshold, rows
from lib.stats import pct

dev = rows("dev")  # the same recording, items and grid as tune-guard-dev
answerable, unanswerable = denominators(dev)
refusal, answer, total = [], [], []
for threshold in GRID:
    refusals, answers = errors(dev, threshold)
    refusal.append(len(refusals) / answerable)
    answer.append(len(answers) / unanswerable)
    total.append(Fraction(len(refusals), answerable) + Fraction(len(answers), unanswerable))  # exact, so ties are real

chosen = pick_threshold(dev)
index = GRID.index(chosen)
refusals, answers = errors(dev, chosen)
print(f"threshold chosen by the dev rule: {chosen:.2f}")
print(f"at the chosen threshold, false refusal rate: {pct(len(refusals), answerable)}")
print(f"at the chosen threshold, false answer rate: {pct(len(answers), unanswerable)}")
print(f"lowest sum of the two rates: {100 * float(min(total)):.1f}%")

# The pick and its rates must be the lines tune-guard-dev prints (its recorded output: pick 0.00, 12.5% and 15.4%),
# so the two examples cannot drift apart. The examples run alone, so the expected values are written here.
assert chosen == 0.0, f"tune-guard-dev's recorded pick is 0.00, not {chosen:.2f}"
assert pct(len(refusals), answerable) == "12.5% (5 of 40)", pct(len(refusals), answerable)
assert pct(len(answers), unanswerable) == "15.4% (2 of 13)", pct(len(answers), unanswerable)
# Raising the threshold only adds declines: refusals never fall, answers never rise. The figure's trade rests on this.
assert all(a <= b for a, b in zip(refusal, refusal[1:])), "a higher threshold must not lower the false refusal rate"
assert all(a >= b for a, b in zip(answer, answer[1:])), "a higher threshold must not raise the false answer rate"
assert total[index] == min(total), "the rule's pick must have the lowest sum on the grid"

fig, ax = new_figure(height=3.0)
ax.plot(GRID, [100 * r for r in refusal], color=ACCENT, label="false refusal rate")
ax.plot(GRID, [100 * a for a in answer], color=INK, label="false answer rate")
ax.plot(GRID, [100 * float(t) for t in total], color=MUTED, linestyle="--", label="sum of the two rates")
ax.axvline(chosen, color=MUTED, linestyle=":", linewidth=1.0)  # the rule's pick, labelled beside the line
ax.text(chosen + 0.2, 3, f"rule's pick: {chosen:.2f}", color=MUTED)  # low on the plot, where no line runs
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(0, 105)
ax.set_xlabel("guard threshold: a top score below it is declined")
ax.set_ylabel("percent of items of that kind")
ax.legend(frameon=False, loc="upper left")  # the top-left corner is empty for every line
save(fig, "guard-threshold")
