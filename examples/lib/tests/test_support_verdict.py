"""The faithfulness verdict reader in lib.judging: SUPPORTED or UNSUPPORTED on the first non-empty line, else None."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.judging import parse_support_verdict


def test_supported_and_unsupported_are_read_from_the_first_line():
    assert parse_support_verdict("VERDICT: SUPPORTED\nEvery claim is in the cited section.") == "SUPPORTED"
    assert parse_support_verdict("VERDICT: UNSUPPORTED\nThe answer adds a flag.") == "UNSUPPORTED"


def test_blank_lines_before_the_verdict_are_skipped():
    assert parse_support_verdict("\n\n  VERDICT: SUPPORTED  \nYes.") == "SUPPORTED"


def test_markdown_emphasis_around_the_line_is_ignored():
    assert parse_support_verdict("**VERDICT: SUPPORTED**\nYes.") == "SUPPORTED"
    assert parse_support_verdict("`VERDICT: UNSUPPORTED`\nNo.") == "UNSUPPORTED"


def test_a_verdict_below_the_first_line_is_not_read():
    assert parse_support_verdict("The answer is fine.\nVERDICT: SUPPORTED") is None


def test_anything_else_reads_as_none():
    assert parse_support_verdict("") is None
    assert parse_support_verdict("VERDICT: PASS") is None
    assert parse_support_verdict("VERDICT: SUPPORTED.") is None
    assert parse_support_verdict("VERDICT: UNSUPPORTED extra") is None
    assert parse_support_verdict("verdict: supported") is None
