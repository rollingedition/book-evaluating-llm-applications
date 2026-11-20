"""The reply contract: the decline phrase, citations, verdict lines, and the checks on a reply.

A model's reply is raw text. This module reads it, never rewrites it: `parse_reply` gives the stripped text,
whether the reply is exactly the decline phrase, and the section IDs it cites in order of appearance.
`format_problems` names what is wrong with a reply, as a sorted list of fixed names. A reply that declines and
also answers is a format problem, not a decline.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from lib.docs import load_sections, versions

DECLINE = "The docs don't say."
CITATION = re.compile(r"\[sec:([a-z][a-z0-9-]*)\]")
VERDICT = re.compile(r"^VERDICT:\s*(PASS|FAIL)$")
PROBLEMS = ("answered-declined-expected", "declined-with-text", "empty", "no-citation", "unknown-section")


@dataclass(frozen=True)
class Reply:
    """A parsed reply: the stripped text, whether it is exactly the decline phrase, and its citations."""

    text: str
    declined: bool
    citations: tuple[str, ...]


def parse_reply(raw: str) -> Reply:
    """Parse a raw reply. Citations are read from the whole text, so both lines of a quote-first reply count."""
    text = raw.strip()
    return Reply(text=text, declined=text == DECLINE, citations=tuple(CITATION.findall(text)))


def format_problems(reply: Reply, *, context_ids: frozenset[str], expect_decline: bool) -> list[str]:
    """The format problems in a reply, sorted, from the fixed names in PROBLEMS.

    `context_ids` are the section IDs that were in the prompt. `expect_decline` is true for an unanswerable item.
    A correct decline on an answerable item is not a format problem; it is counted as a false refusal elsewhere.
    """
    problems: set[str] = set()
    if not reply.text:
        problems.add("empty")
    if DECLINE in reply.text and not reply.declined:
        problems.add("declined-with-text")
    if not reply.declined and reply.text:
        if not reply.citations:
            problems.add("no-citation")
        if any(cid not in context_ids for cid in reply.citations):
            problems.add("unknown-section")
        if expect_decline:
            problems.add("answered-declined-expected")
    return sorted(problems)


def parse_verdict(raw: str) -> str | None:
    """The verdict on the reply's first non-empty line: 'PASS', 'FAIL', or None when that line is not a verdict.

    The judge writes the verdict first and a short reason after it. Markdown emphasis around the line (asterisks,
    backticks) is ignored; nothing else is.
    """
    lines = [line.strip().strip("*`").strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None
    match = VERDICT.match(lines[0])
    return match.group(1) if match else None


CITATION_OUTCOMES = ("supported", "unlisted", "wrong-version", "missing")


def section_ids_by_version() -> dict[str, frozenset[str]]:
    """Each doc version's section IDs, keyed by version in sorted order. The doc files are read on each call."""
    return {version: frozenset(s.section_id for s in load_sections(version)) for version in versions()}


def citation_outcome(
    section_id: str, asked_version: str, listed: frozenset[str], ids: Mapping[str, frozenset[str]]
) -> str:
    """How one cited ID checks out, from the asked version, the item's listed IDs and every version's IDs.

    `listed` holds the item's supporting section IDs for the asked version. The outcomes, from CITATION_OUTCOMES:
    `supported` is a listed ID. `unlisted` is a section of the asked version that the item does not list; it may
    still support the answer, so it is never called wrong. `wrong-version` is a section of another version only.
    `missing` is a section of no version. This checks the ID, not the sentence it is cited for.
    """
    if section_id in ids[asked_version]:
        return "supported" if section_id in listed else "unlisted"
    if any(section_id in found for found in ids.values()):
        return "wrong-version"
    return "missing"


def citation_outcomes(
    reply: Reply, asked_version: str, listed: frozenset[str], ids: Mapping[str, frozenset[str]]
) -> list[str]:
    """The outcome of each citation in a reply, in order of appearance. A repeated ID is counted each time."""
    return [citation_outcome(cid, asked_version, listed, ids) for cid in reply.citations]


ORDER_PROBLEMS = ("citation-first", "stray-line")
CITATION_TOKEN = re.compile(r"\[sec:[a-z][a-z0-9-]*\]")
SENTENCE_END = (".", "?", "!", ":", ")", "`", '"')


def order_problems(text: str) -> list[str]:
    """The order problems in a reply's text, sorted, from the fixed names in ORDER_PROBLEMS.

    The contract puts each sentence first and its citation after it. `citation-first` is a reply whose first line opens
    with a citation. `stray-line` is a line that ends no sentence once its citations are taken out, such as a heading
    fragment or a cut-off line. The check reads only the shape of each line, never what it says. An empty text has no
    order problem; format_problems reports it.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    problems: set[str] = set()
    if lines and CITATION_TOKEN.match(lines[0]):
        problems.add("citation-first")
    for line in lines:
        if not CITATION_TOKEN.sub("", line).strip().endswith(SENTENCE_END):
            problems.add("stray-line")
    return sorted(problems)
