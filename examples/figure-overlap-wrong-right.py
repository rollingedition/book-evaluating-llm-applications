"""Draws each wrong answer's score beside its right answer's score, for every pair, under ROUGE-1 F1 and under BLEU.

The printed counts show the wrong answer scoring higher in every pair under both metrics, and the smallest gap for each
metric is the number the prose rests on. The pairs and the formulas are the ones overlap-misleads scores, copied here so
this example stands on its own."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import json, math, re
from collections import Counter
from pathlib import Path

from lib.figures import ACCENT, INK, MUTED, new_figure, save

PAIRS = json.loads((Path(__file__).resolve().parent / "data" / "overlap-pairs.json").read_text(encoding="utf-8"))
words = lambda text: re.findall(r"[a-z0-9]+", text.lower())  # `lock.json` is two words, as in overlap-misleads


def rouge_1_f1(cand, ref):
    cand, ref = words(cand), words(ref)
    overlap = sum((Counter(cand) & Counter(ref)).values())  # repeats count up to the smaller count
    precision, recall = overlap / len(cand), overlap / len(ref)
    return 2 * precision * recall / (precision + recall) if overlap else 0.0


def bleu(cand, ref):
    """No smoothing: one n-gram order with no match gives 0, as the textbook formula does."""
    cand, ref, score = words(cand), words(ref), 1.0
    for n in range(1, 5):
        c, r = (Counter(zip(*[t[i:] for i in range(n)])) for t in (cand, ref))  # n-grams of each text
        clipped = sum(min(v, r[g]) for g, v in c.items())
        if clipped == 0:
            return 0.0
        score *= clipped / sum(c.values())
    # A candidate shorter than the reference scores less: the brevity penalty.
    return min(1.0, math.exp(1 - len(ref) / len(cand))) * score ** 0.25


scores = {m: {s: [f(p[s], p["reference"]) for p in PAIRS] for s in ("wrong", "right")}
          for m, f in (("ROUGE-1 F1", rouge_1_f1), ("BLEU", bleu))}
fig, axes = new_figure(columns=2, height=2.8)
rows = range(len(PAIRS), 0, -1)  # pair 1 on the top row
for ax, (metric, by_side) in zip(axes, scores.items()):
    ax.hlines(rows, by_side["right"], by_side["wrong"], color=MUTED, linewidth=1)  # the gap the prose names
    ax.scatter(by_side["wrong"], rows, color=ACCENT, marker="o", s=36, zorder=3, label="wrong answer")
    ax.scatter(by_side["right"], rows, color=INK, marker="D", s=24, zorder=3, label="right answer")
    ax.set(title=metric, xlim=(-0.04, 1), xlabel="score, 0 to 1", yticks=rows,  # a BLEU of 0 shows as a marker
           yticklabels=[f"pair {i}" for i in range(1, len(PAIRS) + 1)])
fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=2)

print(f"pairs: {len(PAIRS)}")
for metric, by_side in scores.items():
    gaps = [w - r for w, r in zip(by_side["wrong"], by_side["right"])]
    assert (higher := sum(g > 0 for g in gaps)) == len(PAIRS), f"{metric}: higher in only {higher} pairs"  # every
    print(f"pairs where the wrong answer has the higher {metric}: {higher} of {len(PAIRS)}")
    print(f"smallest wrong-minus-right gap, {metric}: {min(gaps):.3f}")
save(fig, "overlap-wrong-right")
