"""The crossover point and the bootstrap interval of the corrected pass rate in lib.calibration."""
import pytest

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import Judgment, correction_interval, corrected_pass_rate, crossover_pass_rate


def _rows(judge_pass, human_pass, count):
    return [Judgment(id=f"{judge_pass}-{human_pass}-{i}", split="dev", judge_pass=judge_pass, human_pass=human_pass)
            for i in range(count)]


def test_crossover_is_the_rate_the_correction_leaves_unchanged():
    # (1 - 0.6) / (2 - 0.8 - 0.6) = 0.4 / 0.6
    p_star = crossover_pass_rate(0.8, 0.6)
    assert p_star == pytest.approx(0.4 / 0.6)
    assert corrected_pass_rate(p_star, 0.8, 0.6) == pytest.approx(p_star)


def test_correction_lowers_below_the_crossover_and_raises_above_it():
    p_star = crossover_pass_rate(0.8, 0.6)
    assert corrected_pass_rate(0.5, 0.8, 0.6) < 0.5  # 0.25
    assert corrected_pass_rate(0.75, 0.8, 0.6) > 0.75  # 0.875


def test_crossover_refuses_a_judge_whose_rates_sum_to_two():
    with pytest.raises(ValueError):
        crossover_pass_rate(1.0, 1.0)


def test_interval_is_the_same_with_the_same_seed():
    dev = _rows(True, True, 30) + _rows(False, True, 10) + _rows(False, False, 30) + _rows(True, False, 10)
    items = [1.0] * 60 + [0.0] * 40
    assert correction_interval(dev, items) == correction_interval(dev, items)


def test_interval_for_an_exact_judge_is_the_observed_rate_with_no_cap():
    # TPR and TNR are both 1, so the correction is the identity and each resample's rate is its items' rate.
    dev = _rows(True, True, 50) + _rows(False, False, 50)
    items = [1.0] * 60 + [0.0] * 40
    lo, hi, capped, refused = correction_interval(dev, items)
    assert lo < 0.6 < hi
    assert (capped, refused) == (0, 0)


def test_every_resample_hits_the_cap_when_the_observed_rate_is_one_and_TPR_is_below_it():
    # TPR 0.6, TNR 0.9: the correction of an observed rate of 1.0 is 0.9 / 0.5, above 1, so every resample is capped.
    dev = _rows(True, True, 60) + _rows(False, True, 40) + _rows(False, False, 90) + _rows(True, False, 10)
    items = [1.0] * 119
    lo, hi, capped, refused = correction_interval(dev, items)
    assert (lo, hi) == (1.0, 1.0)
    assert (capped, refused) == (2000, 0)


def test_resamples_with_a_small_denominator_are_counted_and_left_out():
    # TPR 0.5 and TNR 0.5 put the denominator near zero, so most resamples fall under 0.1 and are counted as refused.
    dev = _rows(True, True, 50) + _rows(False, True, 50) + _rows(False, False, 50) + _rows(True, False, 50)
    lo, hi, capped, refused = correction_interval(dev, [1.0] * 60 + [0.0] * 40)
    assert refused > 0
    assert capped + refused <= 2000


def test_interval_raises_when_every_resample_is_refused():
    dev = _rows(False, True, 5) + _rows(True, False, 5)  # TPR 0 and TNR 0: TPR + TNR - 1 is -1 in every resample
    with pytest.raises(ValueError):
        correction_interval(dev, [1.0, 0.0])
