"""The decline guard's rule, its error lists and the threshold rule, from lib.guard on hand-made rows."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.guard import Row, denominators, errors, guarded, pick_threshold


def test_a_row_is_guarded_when_declined_or_scored_below_the_threshold():
    assert guarded(Row("q-0001", "answerable", 9.0, declined=True), threshold=1.0)
    assert guarded(Row("q-0002", "answerable", 0.5, declined=False), threshold=1.0)
    assert not guarded(Row("q-0003", "answerable", 2.0, declined=False), threshold=1.0)


def test_denominators_count_only_answerable_and_unanswerable_rows():
    rows = [
        Row("q-0001", "answerable", 2.0, False),
        Row("q-0002", "answerable", 3.0, False),
        Row("q-0003", "unanswerable", 1.0, True),
    ]
    assert denominators(rows) == (2, 1)


def test_errors_list_false_refusals_and_false_answers_by_id():
    rows = [
        Row("q-0001", "answerable", 0.5, False),  # refused by the score: a false refusal at threshold 1.0
        Row("q-0002", "unanswerable", 4.0, False),  # answered: a false answer at threshold 1.0
        Row("q-0003", "unanswerable", 0.5, False),  # refused by the score: correct
    ]
    assert errors(rows, threshold=1.0) == (["q-0001"], ["q-0002"])


def test_threshold_rule_keeps_the_lower_of_two_tied_thresholds():
    # The answerable item scores 3.0 and the unanswerable one 1.0. Any threshold from 1.25 to 3.0 makes no error.
    rows = [Row("q-0001", "answerable", 3.0, False), Row("q-0002", "unanswerable", 1.0, False)]
    assert pick_threshold(rows) == 1.25
