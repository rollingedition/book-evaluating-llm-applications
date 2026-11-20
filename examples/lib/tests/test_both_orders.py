"""The pairwise reader and both orders in lib.judging: the mapping back to the original responses, the four kinds, the
reader's refusals, and the check that the two recordings are the two orders."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import pytest

from lib.judging import BothOrders, both_orders, classify, human_pairs, original, parse_pair_verdict


def test_letter_a_is_response_a_in_order_ab_and_response_b_in_order_ba():
    assert original("A", "ab") == "a"
    assert original("B", "ab") == "b"
    assert original("A", "ba") == "b"
    assert original("B", "ba") == "a"


def test_tie_maps_to_tie_and_no_verdict_maps_to_none():
    assert original("TIE", "ab") == "tie"
    assert original(None, "ba") is None


def test_the_same_original_response_in_both_orders_is_consistent():
    assert classify(original("A", "ab"), original("B", "ba")) == "consistent"  # a in both
    assert classify(original("B", "ab"), original("A", "ba")) == "consistent"  # b in both


def test_the_same_letter_in_both_orders_is_flipped():
    assert classify(original("A", "ab"), original("A", "ba")) == "flipped"  # a, then b
    assert classify(original("B", "ab"), original("B", "ba")) == "flipped"  # b, then a


def test_a_tie_in_either_order_is_a_tie_and_a_missing_verdict_is_unreadable():
    assert classify("tie", "a") == "tie"
    assert classify("b", "tie") == "tie"
    assert classify(None, "a") == "unreadable"
    assert classify("a", None) == "unreadable"


@pytest.mark.parametrize(
    "reply, expected",
    [
        ("VERDICT: A\nReason: x", "A"),
        ("**VERDICT: TIE**\nReason: x", "TIE"),
        ("VERDICT: C\nReason: x", None),
        ("Reason: x\nVERDICT: A", None),
        ("verdict: a", None),
        ("", None),
    ],
)
def test_parse_pair_verdict_reads_a_b_or_tie_on_the_first_line_only(reply, expected):
    assert parse_pair_verdict(reply) == expected


def test_human_pairs_has_both_splits_in_sorted_order_and_one_split_on_request():
    everything = human_pairs()
    assert list(everything) == sorted(everything)
    assert len(human_pairs("dev")) == 75
    assert set(p.split for p in everything.values()) == {"dev", "held-out"}


def test_both_orders_covers_every_pair_once_in_sorted_order():
    ids = list(human_pairs())
    found = both_orders("judge-hs2-pairs-ab", "judge-hs2-pairs-ba", ids)
    assert [f.pair_id for f in found] == sorted(ids)
    assert all(isinstance(f, BothOrders) for f in found)
    assert {f.kind for f in found} <= {"consistent", "flipped", "tie", "unreadable"}


def test_both_orders_refuses_recordings_given_in_the_wrong_order():
    with pytest.raises(ValueError):
        both_orders("judge-hs2-pairs-ba", "judge-hs2-pairs-ab", ["hs2-pref-0001"])
