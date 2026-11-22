"""Draws each answered dev reply's word count in a row for its verdict, with the band edges length-and-verdicts uses.
The prose rests on the printed medians and count, and on the assert that every FAIL reply lies in the PASS range."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import numpy as np

from lib import SEED
from lib.bias import LENGTH_EDGES, band_outcomes, read_verdicts, reply_lengths
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.testset import load_items

ASSISTANT = "assistant-baseline"  # the same reply and judge as length-and-verdicts, on the same dev items
JUDGE = "judge-answers-baseline"

dev = [item.id for item in load_items(split="dev")]  # 80 dev items, sorted by id
lengths = reply_lengths(ASSISTANT, dev)  # answered replies only: declined ones are not in this dict
verdicts = read_verdicts(JUDGE, dev)  # None where the judge's first line is not a verdict
readable = [i for i in lengths if verdicts[i] is not None]  # an unreadable verdict is left out, never counted as FAIL
# length-and-verdicts prints 23 declined and 1 unreadable item; the same items must be left out here.
assert len(dev) - len(lengths) == 23 and len(lengths) - len(readable) == 1, "the same items as length-and-verdicts"
assert sum(o.size for _, o in band_outcomes(lengths, verdicts)) == len(readable), "the bands hold every readable item"

words = {v: [lengths[i] for i in readable if verdicts[i] == v] for v in ("PASS", "FAIL")}
assert min(words["FAIL"]) >= min(words["PASS"]) and max(words["FAIL"]) <= max(words["PASS"]), "every FAIL reply in the PASS range"
print(f"replies read as PASS: {len(words['PASS'])}")
print(f"replies read as FAIL: {len(words['FAIL'])}")
print(f"median words, PASS: {np.median(words['PASS']):g}")
print(f"median words, FAIL: {np.median(words['FAIL']):g}")

rng = np.random.default_rng(SEED)  # the same jitter on every run, so no dot moves between runs
row = {"FAIL": 0, "PASS": 1}  # PASS above FAIL
fig, ax = new_figure(height=2.8)
for verdict, colour in (("PASS", ACCENT), ("FAIL", MUTED)):
    ys = row[verdict] + rng.uniform(-0.15, 0.15, size=len(words[verdict]))  # jitter keeps equal lengths from stacking
    ax.scatter(words[verdict], ys, s=18, color=colour, label=f"{verdict} replies")
    # The median is a short bar on each row, so the rows' centres compare by eye and by the printed values.
    ax.plot([np.median(words[verdict])], [row[verdict]], marker="|", markersize=18, color=INK, linestyle="none",
            label="median" if verdict == "PASS" else None)
for edge in LENGTH_EDGES:
    ax.axvline(edge, color=MUTED, linestyle="--", linewidth=1.0,
               label="band edges, 15 and 30 words" if edge == LENGTH_EDGES[0] else None)
ax.set_yticks([0, 1], ["FAIL", "PASS"])
ax.set_ylim(-0.6, 1.6)
ax.set_xlim(left=0)
ax.grid(axis="y", visible=False)
ax.set_xlabel("reply length, in words")
ax.set_ylabel("judge's verdict")
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=4, fontsize=8)  # above the rows, clear of the dots
save(fig, "length-by-verdict")
