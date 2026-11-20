"""The benchmark loaders and scorers in lib.bench."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.bench import (load_gsm8k, load_truthfulqa, load_truthfulqa_shuffled, normal_number, parse_gsm8k, parse_tqa,
                       score_gsm8k, score_truthfulqa, shuffle_order)


def test_normal_number_drops_commas_and_a_trailing_point_zero():
    assert normal_number("1,200") == "1200"
    assert normal_number("540.0") == "540"
    assert normal_number("3.50") == "3.5"
    assert normal_number("100") == "100"


def test_parse_gsm8k_takes_the_last_hash_line_over_a_later_number():
    assert parse_gsm8k("I get 12.\n#### 540\nSo 9 is not the answer, 7 is") == "540"


def test_parse_gsm8k_falls_back_to_the_last_number_and_strips_the_comma():
    assert parse_gsm8k("Each sprint is 60 meters. Final answer: 1,200") == "1200"
    assert parse_gsm8k("Total is 540, so the answer is 540.") == "540"


def test_parse_gsm8k_returns_none_without_a_number():
    assert parse_gsm8k("I cannot tell.") is None


def test_parse_tqa_reads_the_first_line_and_refuses_a_letter_past_the_options():
    assert parse_tqa("B", 4) == "B"
    assert parse_tqa("Answer: C\n", 4) == "C"
    assert parse_tqa("E. Unknown.", 4) is None
    assert parse_tqa("   \n", 4) is None


def test_an_unreadable_reply_is_never_counted_wrong():
    rows = [{"id": "x-1", "reference": "5"}, {"id": "x-2", "reference": "6"}]
    scored = score_gsm8k(rows, {"x-1": "no number here", "x-2": "#### 6"})
    assert scored == [("x-1", None, None), ("x-2", "6", True)]


def test_truthfulqa_scores_readable_letters_and_leaves_the_rest_unscored():
    rows = [{"id": "t-1", "choices": ["a", "b"], "correct": "B"}, {"id": "t-2", "choices": ["a", "b"], "correct": "A"}]
    scored = score_truthfulqa(rows, {"t-1": "B", "t-2": "Z"})
    assert scored == [("t-1", "B", True), ("t-2", None, None)]


def test_the_samples_load_sorted_with_one_row_per_item():
    gsm = load_gsm8k()
    tqa = load_truthfulqa()
    assert len(gsm) == 100 and len(tqa) == 100
    assert [row["id"] for row in gsm] == sorted(row["id"] for row in gsm)
    assert all(row["reference"].lstrip("-").isdigit() for row in gsm)
    assert all(row["correct"] in "ABCDEFGHIJ"[:len(row["choices"])] for row in tqa)


def test_shuffle_order_is_a_permutation_and_repeats_for_the_same_item():
    order = shuffle_order("truthfulqa-val-0002", 4)
    assert sorted(order) == [0, 1, 2, 3]
    assert shuffle_order("truthfulqa-val-0002", 4) == order


def test_shuffled_items_are_deterministic_and_keep_their_option_set():
    first = load_truthfulqa_shuffled()
    second = load_truthfulqa_shuffled()
    assert first == second
    original = {row["id"]: row for row in load_truthfulqa()}
    for row in first:
        source = original[row["id"]]
        assert sorted(row["choices"]) == sorted(source["choices"])
        assert sorted(row["order"]) == list(range(len(source["choices"])))
        assert [source["choices"][i] for i in row["order"]] == row["choices"]
        # the correct option's text is the same, at its new letter
        assert row["choices"][row["correct_index"]] == source["choices"][ord(source["correct"]) - 65]
        assert row["correct"] == chr(65 + row["correct_index"])


def test_over_the_sample_the_correct_letter_is_not_always_a():
    letters = [row["correct"] for row in load_truthfulqa_shuffled()]
    assert len(letters) == 100
    assert letters.count("A") < 100
    assert len(set(letters)) >= 3
