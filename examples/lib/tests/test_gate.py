"""The gate: fails only when the upper bound of the paired drop is below minus the threshold."""
import pytest

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.gate import FAIL, PASS, gate
from lib.stats import bootstrap_mean


def test_identical_runs_pass_with_no_difference():
    values = [1, 0, 1, 1, 0, 1, 1, 1]
    result = gate(values, values, threshold_points=5)
    assert result.decision == PASS
    assert result.difference == 0.0
    assert result.n == len(values)


def test_large_drop_fails():
    baseline = [1] * 80
    candidate = [1] * 40 + [0] * 40  # half the items lost: a drop of 50 points
    result = gate(baseline, candidate, threshold_points=5)
    assert result.decision == FAIL
    assert result.difference == pytest.approx(-0.5)
    assert result.hi < -0.05


def test_drop_whose_upper_bound_reaches_the_threshold_passes():
    # One item of twenty flips: a point drop of five, but the interval's upper bound is 0, above minus five.
    baseline = [1] * 10 + [0] * 10
    candidate = [0] + [1] * 9 + [0] * 10
    result = gate(baseline, candidate, threshold_points=5)
    assert result.difference == pytest.approx(-0.05)
    assert result.hi > -0.05
    assert result.decision == PASS


def test_interval_is_the_seeded_bootstrap_of_the_paired_difference():
    baseline = [1, 1, 0, 1, 0, 1, 1, 0, 1, 1]
    candidate = [1, 0, 0, 1, 0, 1, 0, 0, 1, 1]
    result = gate(baseline, candidate, threshold_points=5)
    expected = bootstrap_mean([c - b for b, c in zip(baseline, candidate)], level=0.95)
    assert (result.lo, result.hi) == expected
    assert result.level == pytest.approx(0.95)


def test_several_comparisons_use_the_adjusted_level_and_a_wider_interval():
    baseline = [1, 1, 0, 1, 0, 1, 1, 0, 1, 1] * 4
    candidate = [1, 0, 0, 1, 0, 1, 0, 0, 1, 1] * 4
    one = gate(baseline, candidate, threshold_points=5, comparisons=1)
    three = gate(baseline, candidate, threshold_points=5, comparisons=3)
    assert three.level == pytest.approx(1 - 0.05 / 3)
    assert three.lo <= one.lo and three.hi >= one.hi


def test_same_inputs_give_the_same_interval():
    baseline = [1, 0, 1, 1, 0, 1, 0, 1]
    candidate = [1, 0, 0, 1, 0, 1, 0, 0]
    first = gate(baseline, candidate, threshold_points=5)
    second = gate(baseline, candidate, threshold_points=5)
    assert (first.lo, first.hi, first.decision) == (second.lo, second.hi, second.decision)


@pytest.mark.parametrize(
    "baseline, candidate, threshold, comparisons",
    [
        ([1, 0], [1], 5, 1),  # lengths differ
        ([], [], 5, 1),  # no items
        ([1, 2], [1, 0], 5, 1),  # not a pass or fail
        ([1, 0], [1, 0], 0, 1),  # a threshold must be above 0
        ([1, 0], [1, 0], 5, 0),  # at least one comparison
    ],
)
def test_bad_inputs_are_refused(baseline, candidate, threshold, comparisons):
    with pytest.raises(ValueError):
        gate(baseline, candidate, threshold_points=threshold, comparisons=comparisons)
