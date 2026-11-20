"""Agreement between the judge and human ratings, Cohen's kappa, TPR and TNR, and a corrected pass rate.

The calibration set is HelpSteer2's ratings: each row is a response to a request, rated by people on five scores.
A human PASS is correctness 3 or 4; FAIL is 0 to 2 (plan section 9). The judge's verdict on the same row is the
reference-free correctness verdict recorded in `judge-helpsteer2`. PASS is the positive class throughout: TPR is
the share of human PASS rows the judge also passes, and TNR the share of human FAIL rows it also fails.

Everything here is plain Python on counts, so the same counts always give the same numbers.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from lib import SEED
from lib.contract import parse_verdict
from lib.prompts import HS2_SHA256
from lib.replay import ReplayModel
from lib.stats import RESAMPLES

DATA = Path(__file__).resolve().parent.parent / "data"
RATINGS = DATA / "helpsteer2" / "ratings.jsonl"
JUDGE_RECORDING = "judge-helpsteer2"
HUMAN_PASS_MIN_CORRECTNESS = 3  # scores 3 and 4 are PASS (plan section 9)
MIN_DENOMINATOR = 0.1  # the correction is refused when TPR + TNR - 1 is below this (plan section 6.2)


@dataclass(frozen=True)
class Judgment:
    """One calibration row: its id and split, the judge's verdict as a bool, and the human PASS as a bool."""
    id: str
    split: str
    judge_pass: bool
    human_pass: bool


@dataclass(frozen=True)
class Counts:
    """The 2 x 2 table of judge against human. Each cell is a count of rows."""
    tp: int  # judge PASS, human PASS
    fp: int  # judge PASS, human FAIL
    fn: int  # judge FAIL, human PASS
    tn: int  # judge FAIL, human FAIL

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn


def helpsteer2_judgments(split: str | None = None) -> list[Judgment]:
    """The judge's verdict and the human PASS for each calibration row, sorted by id; `split` keeps one split.

    The recording is read with the HelpSteer2 prompt's hash, not the reference-guided prompt's. A reply with no readable
    verdict is an error, never a FAIL.
    """
    replies = ReplayModel(JUDGE_RECORDING, HS2_SHA256)  # the prompt hash must match the judge's manifest
    rows = [json.loads(line) for line in RATINGS.read_text(encoding="utf-8").splitlines() if line.strip()]
    found: list[Judgment] = []
    for row in sorted(rows, key=lambda row: row["id"]):
        if split is not None and row["split"] != split:
            continue
        verdict = parse_verdict(replies.reply(row["id"], 0))
        if verdict is None:
            raise ValueError(f"judge recording {JUDGE_RECORDING!r} has no readable verdict for {row['id']!r}")
        found.append(
            Judgment(
                id=row["id"],
                split=row["split"],
                judge_pass=verdict == "PASS",
                human_pass=row["correctness"] >= HUMAN_PASS_MIN_CORRECTNESS,
            )
        )
    return found


def readable_verdicts(
    recording: str, item_ids: Sequence[str], prompt_sha256: str
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """The verdicts that can be read from a recording, plus the replies that cannot, for the caller to print.

    Returns (verdicts keyed in sorted id order, unreadable) where unreadable lists (item id, first line of the reply) for
    each reply whose first line is not a verdict. Unreadable replies are left out of the verdicts, never counted as FAIL,
    and the caller must print them so the exclusion is visible.
    """
    replies = ReplayModel(recording, prompt_sha256)  # the prompt hash must match the judge's manifest
    found: dict[str, str] = {}
    unreadable: list[tuple[str, str]] = []
    for item_id in sorted(item_ids):
        raw = replies.reply(item_id, 0)
        verdict = parse_verdict(raw)
        if verdict is None:
            first = next((line.strip() for line in raw.splitlines() if line.strip()), "")
            unreadable.append((item_id, first))
        else:
            found[item_id] = verdict
    return found, unreadable


def confusion(judgments: Sequence[Judgment]) -> Counts:
    """The 2 x 2 counts of judge against human over the given rows."""
    tp = sum(1 for j in judgments if j.judge_pass and j.human_pass)
    fp = sum(1 for j in judgments if j.judge_pass and not j.human_pass)
    fn = sum(1 for j in judgments if not j.judge_pass and j.human_pass)
    tn = sum(1 for j in judgments if not j.judge_pass and not j.human_pass)
    return Counts(tp=tp, fp=fp, fn=fn, tn=tn)


def agreement(counts: Counts) -> float:
    """The share of rows where judge and human give the same verdict."""
    if counts.n == 0:
        raise ValueError("agreement needs at least one row")
    return (counts.tp + counts.tn) / counts.n


def chance_agreement(counts: Counts) -> float:
    """The agreement two raters would reach by chance, given how often each one says PASS."""
    judge_pass = (counts.tp + counts.fp) / counts.n
    human_pass = (counts.tp + counts.fn) / counts.n
    return judge_pass * human_pass + (1 - judge_pass) * (1 - human_pass)


def cohens_kappa(counts: Counts) -> float:
    """Cohen's kappa for two binary raters: agreement beyond chance, scaled to 1 at perfect agreement.

    Written out here rather than taken from a library, so the formula is visible: (p_o - p_e) / (1 - p_e).
    """
    p_o = agreement(counts)
    p_e = chance_agreement(counts)
    if p_e == 1.0:
        raise ValueError("kappa is undefined when chance agreement is 1")
    return (p_o - p_e) / (1 - p_e)


def tpr(counts: Counts) -> float:
    """The true positive rate: of the human PASS rows, the share the judge also passes."""
    if counts.tp + counts.fn == 0:
        raise ValueError("TPR needs at least one human PASS row")
    return counts.tp / (counts.tp + counts.fn)


def tnr(counts: Counts) -> float:
    """The true negative rate: of the human FAIL rows, the share the judge also fails."""
    if counts.tn + counts.fp == 0:
        raise ValueError("TNR needs at least one human FAIL row")
    return counts.tn / (counts.tn + counts.fp)


def corrected_pass_rate(observed: float, tpr_value: float, tnr_value: float) -> float:
    """The observed judge pass rate, corrected for the judge's known errors, clipped to [0, 1].

    The correction is (observed + TNR - 1) / (TPR + TNR - 1). It is an algebraic correction for a judge whose TPR and
    TNR are known: it assumes they hold for the set being corrected. It is refused when TPR + TNR - 1 is below
    MIN_DENOMINATOR, since a near-zero denominator turns small errors into large corrections.
    """
    denominator = tpr_value + tnr_value - 1.0
    if denominator < MIN_DENOMINATOR:
        raise ValueError(
            f"corrected pass rate refused: TPR + TNR - 1 is {denominator:.3f}, below {MIN_DENOMINATOR}"
        )
    corrected = (observed + tnr_value - 1.0) / denominator
    return min(1.0, max(0.0, corrected))


def crossover_pass_rate(tpr_value: float, tnr_value: float) -> float:
    """The observed pass rate at which the correction leaves the rate unchanged: (1 - TNR) / (2 - TPR - TNR).

    Below this rate the correction lowers the observed rate, and above it the correction raises it. At this rate the
    judge's true passes and false passes account for the observed rate exactly, so the correction returns it as it is.
    """
    denominator = 2.0 - tpr_value - tnr_value
    if denominator <= 0.0:
        raise ValueError("the crossover point needs TPR + TNR below 2")
    return (1.0 - tnr_value) / denominator


def correction_interval(
    dev: Sequence[Judgment], item_passes: Sequence[float], seed: int = SEED
) -> tuple[float, float, int, int]:
    """The 95% percentile bootstrap interval of the corrected pass rate, with two counts over all resamples.

    Each resample draws the dev rows with replacement, which gives its TPR and TNR, and draws the readable items with
    replacement, which gives its observed rate. The second count is how many resamples reach the 100% cap: their
    unclipped rate is 1 or more, and the rate is clipped to [0, 1] as corrected_pass_rate clips it. The last count is how
    many resamples are refused, because they hold no PASS or no FAIL row, or their TPR + TNR - 1 is below
    MIN_DENOMINATOR. The interval is taken over the rest.
    One generator made from seed draws both groups.
    """
    judge = np.array([j.judge_pass for j in dev], dtype=bool)
    human = np.array([j.human_pass for j in dev], dtype=bool)
    items = np.asarray(item_passes, dtype=float)
    if judge.size == 0 or items.size == 0:
        raise ValueError("the correction interval needs dev rows and readable items")
    rng = np.random.default_rng(seed)
    dev_picks = rng.integers(0, judge.size, size=(RESAMPLES, judge.size))
    item_picks = rng.integers(0, items.size, size=(RESAMPLES, items.size))
    judge_s, human_s = judge[dev_picks], human[dev_picks]
    human_pass_s = human_s.sum(axis=1)
    human_fail_s = (~human_s).sum(axis=1)
    tpr_s = (judge_s & human_s).sum(axis=1) / np.maximum(human_pass_s, 1)  # a resample with no PASS row is refused below
    tnr_s = (~judge_s & ~human_s).sum(axis=1) / np.maximum(human_fail_s, 1)
    observed_s = items[item_picks].mean(axis=1)
    denominator = tpr_s + tnr_s - 1.0
    usable = (human_pass_s > 0) & (human_fail_s > 0) & (denominator >= MIN_DENOMINATOR)
    raw = (observed_s[usable] + tnr_s[usable] - 1.0) / denominator[usable]
    if raw.size == 0:
        raise ValueError(f"every resample is refused: TPR + TNR - 1 is below {MIN_DENOMINATOR}")
    lo, hi = np.quantile(np.clip(raw, 0.0, 1.0), [0.025, 0.975])
    return float(lo), float(hi), int(np.sum(raw >= 1.0)), int(np.sum(~usable))
