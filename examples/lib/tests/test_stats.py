"""The printing helpers and the seeded bootstrap in lib.stats."""
import pytest

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.stats import bootstrap_difference, bootstrap_mean, interval_pct, interval_points, pct


def test_pct_prints_the_rate_and_its_counts():
    assert pct(13, 20) == "65.0% (13 of 20)"


def test_pct_refuses_a_zero_denominator():
    with pytest.raises(ValueError):
        pct(0, 0)


def test_interval_helpers_round_and_sign_the_way_the_book_prints_them():
    assert interval_pct(0.45, 0.85) == "[45.0%, 85.0%]"
    assert interval_points(-0.04, 0.12) == "[-4.0, +12.0] points"


def test_bootstrap_of_constant_values_is_that_value():
    assert bootstrap_mean([0.25] * 12) == (0.25, 0.25)


def test_bootstrap_is_the_same_on_every_call():
    values = [1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0]
    assert bootstrap_mean(values) == bootstrap_mean(values)


def test_bootstrap_interval_brackets_the_mean_and_widens_with_the_level():
    values = [1.0] * 6 + [0.0] * 4
    lo, hi = bootstrap_mean(values)
    assert lo <= 0.6 <= hi
    wide_lo, wide_hi = bootstrap_mean(values, level=0.99)
    assert wide_lo <= lo and wide_hi >= hi


def test_bootstrap_refuses_empty_and_two_dimensional_input():
    with pytest.raises(ValueError):
        bootstrap_mean([])
    with pytest.raises(ValueError):
        bootstrap_mean([[1.0, 0.0]])


def test_difference_of_constant_groups_is_the_difference_of_their_means():
    assert bootstrap_difference([0.25] * 12, [0.75] * 9) == (0.5, 0.5)


def test_difference_interval_is_second_minus_first_and_is_the_same_on_every_call():
    first = [1.0, 0.0, 0.0, 0.0]
    second = [1.0, 1.0, 1.0, 0.0]
    lo, hi = bootstrap_difference(first, second)
    assert lo <= 0.5 <= hi
    assert (lo, hi) == bootstrap_difference(first, second)


def test_difference_refuses_an_empty_group():
    with pytest.raises(ValueError):
        bootstrap_difference([], [1.0])
