"""The chapter 7 helpers in lib.bias: length bands, verdicts that may be unreadable, the flip direction, and the band gap."""
import numpy as np
import pytest

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.bias import (
    LENGTH_BANDS,
    band_outcomes,
    flip_direction,
    gap_interval,
    length_band,
    paired_passes,
    read_verdicts,
    reply_lengths,
    same_model_count,
    unreadable_count,
    word_count,
)
from lib.judging import BothOrders


def test_word_count_splits_on_any_run_of_whitespace():
    assert word_count("two  words\nand a third") == 5


def test_length_band_includes_the_lower_edge_of_each_band():
    assert [length_band(words) for words in (0, 14, 15, 29, 30, 200)] == [
        LENGTH_BANDS[0],
        LENGTH_BANDS[0],
        LENGTH_BANDS[1],
        LENGTH_BANDS[1],
        LENGTH_BANDS[2],
        LENGTH_BANDS[2],
    ]


def test_length_band_refuses_a_negative_count():
    with pytest.raises(ValueError):
        length_band(-1)


def test_band_outcomes_leave_out_unreadable_and_never_count_them_as_fail():
    lengths = {"q-0001": 5, "q-0002": 20, "q-0003": 40, "q-0004": 41}
    verdicts = {"q-0001": "PASS", "q-0002": None, "q-0003": "FAIL", "q-0004": "PASS"}
    bands = dict(band_outcomes(lengths, verdicts))
    assert bands[LENGTH_BANDS[0]].tolist() == [1.0]
    assert bands[LENGTH_BANDS[1]].tolist() == []
    assert bands[LENGTH_BANDS[2]].tolist() == [0.0, 1.0]


def test_band_outcomes_refuse_an_item_with_no_verdict_entry():
    with pytest.raises(KeyError):
        band_outcomes({"q-0001": 5}, {})


def test_read_verdicts_returns_none_for_the_unreadable_line_in_sorted_order():
    found = read_verdicts("judge-answers-baseline", ["q-0043", "q-0001"])
    assert list(found) == ["q-0001", "q-0043"]
    assert found["q-0043"] is None
    assert found["q-0001"] in {"PASS", "FAIL"}


def test_reply_lengths_leave_out_declined_replies_and_keep_answered_ones_sorted():
    # q-0004 is a recorded decline in assistant-baseline; q-0001 and q-0003 are answers
    lengths = reply_lengths("assistant-baseline", ["q-0004", "q-0003", "q-0001"])
    assert list(lengths) == ["q-0001", "q-0003"]
    assert all(words > 0 for words in lengths.values())


def test_flip_direction_names_the_position_that_won_both_times():
    first = BothOrders("p-1", "a", "b", "flipped")
    second = BothOrders("p-2", "b", "a", "flipped")
    assert flip_direction(first) == "first"
    assert flip_direction(second) == "second"


def test_flip_direction_is_none_for_any_other_kind():
    assert flip_direction(BothOrders("p-3", "a", "a", "consistent")) is None
    assert flip_direction(BothOrders("p-4", "a", None, "unreadable")) is None


def test_unreadable_count_counts_the_partial_verdict_in_the_baseline():
    assert unreadable_count(["judge-answers-baseline"], ["q-0043"]) == (1, 1)


def test_same_model_count_is_false_for_the_second_model_assistant():
    assert same_model_count(["judge-answers-baseline", "judge-answers-second-model"]) == (1, 2)


def test_paired_passes_leave_out_an_item_unreadable_in_either_recording():
    both, first, second = paired_passes(
        "judge-answers-baseline", "judge-answers-second-model", ["q-0043", "q-0003", "q-0001"]
    )
    assert "q-0043" not in both
    assert both == sorted(both)
    assert first.size == second.size == len(both)


def test_gap_interval_is_zero_wide_when_both_groups_are_constant_and_equal():
    low = np.ones(5)
    high = np.ones(7)
    assert gap_interval(low, high) == (0.0, 0.0)


def test_gap_interval_brackets_the_difference_of_the_group_means():
    low = np.array([0.0, 0.0, 0.0, 1.0] * 5)
    high = np.array([1.0, 1.0, 1.0, 0.0] * 5)
    lo, hi = gap_interval(low, high)
    assert lo < 0.5 < hi
