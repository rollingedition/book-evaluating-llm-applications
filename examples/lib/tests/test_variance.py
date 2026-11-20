"""The per-item verdict counts over the variance set, from raw replies and from the variance judge's recording."""
import pytest

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.variance import (
    ItemVerdicts,
    interval_width_points,
    item_pass_counts,
    items_needed,
    items_needed_at,
    paired_difference_variance,
    smallest_difference_at,
    smallest_difference_points,
    summarize,
    z_sum,
)

PASS = "VERDICT: PASS\nThe reply states the default."
FAIL = "VERDICT: FAIL\nThe reply states the wrong default."
PARTIAL = "VERDICT: PARTIAL\nThe reply covers one reading only."


def test_counts_the_passes_among_five_samples():
    rows = summarize({"q-0001": {1: PASS, 2: FAIL, 3: PASS, 4: PASS, 5: FAIL}})
    assert rows == [ItemVerdicts("q-0001", 3, 5, ())]


def test_an_item_with_some_passes_and_some_fails_is_flaky():
    assert summarize({"q-0004": {1: PASS, 2: FAIL, 3: PASS, 4: PASS, 5: PASS}})[0].flaky is True


def test_an_item_that_always_passes_or_always_fails_is_not_flaky():
    rows = summarize({"q-0005": {1: PASS, 2: PASS, 3: PASS, 4: PASS, 5: PASS}, "q-0006": {1: FAIL, 2: FAIL, 3: FAIL,
                                                                                    4: FAIL, 5: FAIL}})
    assert [row.flaky for row in rows] == [False, False]


def test_an_unreadable_reply_is_left_out_and_never_counted_as_fail():
    row = summarize({"q-0003": {1: PASS, 2: PARTIAL, 3: PASS, 4: PASS, 5: PASS}})[0]
    assert row == ItemVerdicts("q-0003", 4, 4, (2,))
    assert row.complete is False
    assert row.flaky is False


def test_rows_come_back_sorted_by_item_id():
    rows = summarize({"q-0009": {1: PASS}, "q-0002": {1: FAIL}})
    assert [row.item_id for row in rows] == ["q-0002", "q-0009"]


def test_the_recording_gives_the_five_samples_of_each_item_in_id_order():
    rows = item_pass_counts("judge-answers-variance", ["q-0043", "q-0001"])
    assert [row.item_id for row in rows] == ["q-0001", "q-0043"]
    assert all(row.readable + len(row.unreadable) == 5 for row in rows)
    assert rows[1].unreadable == (1, 4)
    assert rows[1].readable == 3


def test_a_recording_without_the_asked_samples_raises():
    with pytest.raises(KeyError):
        item_pass_counts("judge-answers-baseline", ["q-0001"])  # the baseline holds sample 0 only


def test_paired_difference_variance_is_discordance_less_squared_mean():
    # d = [0, 1, 0, -1]: mean 0, mean of d squared 0.5, so the variance is 0.5
    assert paired_difference_variance([1, 0, 0, 1], [1, 1, 0, 0]) == pytest.approx(0.5)


def test_a_constant_paired_difference_has_no_variance():
    # d = [1, 1]: the discordance is all of it and the squared mean cancels it
    assert paired_difference_variance([0, 0], [1, 1]) == pytest.approx(0.0)


def test_items_needed_follows_the_normal_formula_rounded_up():
    # (1.96 + 0.84)^2 * 0.01 / 0.05^2 = 31.4 and / 0.10^2 = 7.85
    assert items_needed(0.01, 5.0) == 32
    assert items_needed(0.01, 10.0) == 8


def test_the_smallest_difference_and_the_interval_width_at_one_item():
    # with var_d 0.01 and one item, the standard error is 0.1: 2.80 * 10 and 2 * 1.96 * 10 points
    assert smallest_difference_points(0.01, 1) == pytest.approx(28.0, abs=0.05)
    assert interval_width_points(0.01, 1) == pytest.approx(39.2, abs=0.05)


def test_z_sum_is_the_normal_quantiles_for_the_level_and_the_power():
    assert z_sum() == pytest.approx(2.8016, abs=1e-4)  # 1.96 + 0.8416
    assert z_sum(0.05 / 3) == pytest.approx(3.2355, abs=1e-3)  # 2.3939 + 0.8416


def test_items_needed_at_the_default_level_matches_items_needed():
    assert items_needed_at(0.01, 5.0) == items_needed(0.01, 5.0) == 32
    assert items_needed_at(0.01, 10.0) == items_needed(0.01, 10.0) == 8


def test_items_needed_at_the_bonferroni_level_is_larger():
    # z_sum(0.05 / 3) squared is 10.47; times 0.01 / 0.05^2 is 41.9, rounded up
    assert items_needed_at(0.01, 5.0, 0.05 / 3) == 42


def test_smallest_difference_at_the_default_level_matches_the_points_function():
    assert smallest_difference_at(0.01, 1) == pytest.approx(smallest_difference_points(0.01, 1), abs=1e-9)
    # 3.2355 * sqrt(0.1006 / 40) is 16.2 points: what 40 items detect at the held-out level
    assert smallest_difference_at(0.1006, 40, 0.05 / 3) == pytest.approx(16.2, abs=0.05)
