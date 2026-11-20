"""The judge-against-human counts, agreement, kappa, TPR, TNR and the corrected pass rate in lib.calibration."""
import pytest

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import (
    Counts,
    Judgment,
    agreement,
    cohens_kappa,
    confusion,
    corrected_pass_rate,
    readable_verdicts,
    tnr,
    tpr,
)
from lib.prompts import REF_SHA256


def _rows(judge_pass, human_pass, count):
    tag = f"{judge_pass}-{human_pass}"
    return [Judgment(id=f"{tag}-{i}", split="dev", judge_pass=judge_pass, human_pass=human_pass) for i in range(count)]


def test_confusion_counts_each_cell():
    rows = _rows(True, True, 3) + _rows(True, False, 1) + _rows(False, True, 2) + _rows(False, False, 4)
    assert confusion(rows) == Counts(tp=3, fp=1, fn=2, tn=4)


def test_agreement_and_kappa_on_a_known_table():
    counts = Counts(tp=40, fp=10, fn=10, tn=40)
    assert agreement(counts) == pytest.approx(0.8)
    assert cohens_kappa(counts) == pytest.approx(0.6)  # chance agreement is 0.5


def test_perfect_agreement_has_kappa_one():
    assert cohens_kappa(Counts(tp=5, fp=0, fn=0, tn=5)) == pytest.approx(1.0)


def test_agreement_refuses_an_empty_table():
    with pytest.raises(ValueError):
        agreement(Counts(tp=0, fp=0, fn=0, tn=0))


def test_tpr_and_tnr_are_the_rates_of_the_human_classes():
    counts = Counts(tp=9, fp=2, fn=1, tn=8)
    assert tpr(counts) == pytest.approx(0.9)
    assert tnr(counts) == pytest.approx(0.8)


def test_corrected_pass_rate_is_the_algebraic_correction():
    # (0.5 + 0.8 - 1) / (0.9 + 0.8 - 1) = 0.3 / 0.7
    assert corrected_pass_rate(0.5, 0.9, 0.8) == pytest.approx(0.3 / 0.7)


def test_corrected_pass_rate_is_clipped_to_the_unit_interval():
    assert corrected_pass_rate(0.0, 0.9, 0.8) == 0.0
    assert corrected_pass_rate(1.0, 0.9, 0.6) == 1.0


def test_corrected_pass_rate_is_refused_when_the_denominator_is_small():
    with pytest.raises(ValueError):
        corrected_pass_rate(0.5, 0.5, 0.55)  # TPR + TNR - 1 = 0.05, below 0.1


def test_readable_verdicts_reads_the_recording_with_its_prompt_hash():
    found, unreadable = readable_verdicts("judge-answers-baseline", ["q-0002", "q-0001"], REF_SHA256)
    assert list(found) == ["q-0001", "q-0002"]
    assert unreadable == []
