"""The reply and verdict formats the judge and the assistant must keep, from lib.contract."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import format_problems, parse_reply, parse_verdict


def test_verdict_is_read_from_the_first_line_only():
    assert parse_verdict("VERDICT: PASS\nThe answer matches.") == "PASS"
    assert parse_verdict("**VERDICT: FAIL**\nNo.") == "FAIL"
    assert parse_verdict("The answer matches.\nVERDICT: PASS") is None


def test_a_line_that_is_not_a_verdict_reads_as_none():
    assert parse_verdict("PASS") is None
    assert parse_verdict("") is None


def test_reply_reads_its_citations_and_the_decline_phrase():
    reply = parse_reply("Yes. [sec:sync-default] [sec:diff-preview]")
    assert reply.citations == ("sync-default", "diff-preview")
    assert reply.declined is False
    assert parse_reply("The docs don't say.").declined is True


def test_a_clean_cited_answer_has_no_format_problems():
    reply = parse_reply("Yes. [sec:sync-default]")
    assert format_problems(reply, context_ids=frozenset({"sync-default"}), expect_decline=False) == []


def test_format_problems_name_each_fault_once_sorted():
    empty = parse_reply("")
    assert format_problems(empty, context_ids=frozenset(), expect_decline=False) == ["empty"]
    uncited = parse_reply("Yes.")
    assert format_problems(uncited, context_ids=frozenset({"sync-default"}), expect_decline=False) == ["no-citation"]
    unknown = parse_reply("Yes. [sec:other-section]")
    assert format_problems(unknown, context_ids=frozenset({"sync-default"}), expect_decline=False) == ["unknown-section"]
    answered = parse_reply("Yes. [sec:sync-default]")
    assert format_problems(answered, context_ids=frozenset({"sync-default"}), expect_decline=True) == [
        "answered-declined-expected"
    ]
