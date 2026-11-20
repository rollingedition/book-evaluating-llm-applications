"""Reading judge verdicts and the paired difference type in lib.judging."""
import numpy as np

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.judging import Paired, passed, verdicts


def test_passed_is_one_for_pass_and_zero_for_fail_in_key_order():
    found = {"q-0002": "FAIL", "q-0001": "PASS", "q-0003": "PASS"}
    assert passed(found).tolist() == [0.0, 1.0, 1.0]


def test_paired_difference_is_second_minus_first():
    result = Paired(
        n=4,
        first=np.array([1.0, 0.0, 1.0, 0.0]),
        second=np.array([1.0, 1.0, 0.0, 0.0]),
        diff_lo=-0.5,
        diff_hi=0.5,
    )
    assert result.difference == 0.0


def test_verdicts_read_the_recorded_judge_in_sorted_id_order():
    found = verdicts("judge-answers-baseline", ["q-0003", "q-0001"])
    assert list(found) == ["q-0001", "q-0003"]
    assert set(found.values()) <= {"PASS", "FAIL"}
