"""The test set's item schema (plan section 3.2) and its loader.

One JSON object per line in examples/data/testset.jsonl. Each item is validated with `extra="forbid"`; errors are
reported without URLs (`include_url=False`), so a message never carries the pydantic version.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, model_validator
from typing_extensions import Annotated

from lib.docs import load_sections, versions

TESTSET = Path(__file__).resolve().parent.parent / "data" / "testset.jsonl"
PLANTED_WHY = ("false-premise", "near-miss-term", "version-swap", "stale-answer", "ambiguous-target")
ItemId = Annotated[str, StringConstraints(pattern=r"^q-[0-9]{4}$")]


class SectionRef(BaseModel):
    """A supporting section: its version and ID."""

    model_config = ConfigDict(extra="forbid")
    version: Literal["1.0", "1.1", "2.0"]
    section_id: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]


class Item(BaseModel):
    """One test question, with its written reference and supporting sections."""

    model_config = ConfigDict(extra="forbid")
    id: ItemId
    question: Annotated[str, StringConstraints(min_length=1, max_length=400, pattern=r"^[\x20-\x7e]+$")]
    version: Literal["1.0", "1.1", "2.0"]
    kind: Literal["answerable", "unanswerable", "version-dependent", "ambiguous"]
    reference_answer: str | None
    supporting_sections: list[SectionRef] = Field(default_factory=list)
    split: Literal["dev", "held-out"]
    planted: bool
    planted_why: Literal["false-premise", "near-miss-term", "version-swap", "stale-answer", "ambiguous-target"] | None
    twin_of: ItemId | None

    @model_validator(mode="after")
    def _kind_rules(self) -> "Item":
        if (self.kind == "unanswerable") != (self.reference_answer is None):
            raise ValueError("reference_answer is null exactly when kind is unanswerable")
        if self.kind != "unanswerable" and not self.supporting_sections:
            raise ValueError("an answerable, version-dependent or ambiguous item lists at least one section")
        if self.kind == "ambiguous" and self.reference_answer is not None:
            if not self.reference_answer.startswith("Reading 1:"):
                raise ValueError("an ambiguous reference starts with 'Reading 1:'")
        if any(s.version != self.version for s in self.supporting_sections) and self.kind != "unanswerable":
            raise ValueError("supporting sections share the item's version unless the item is unanswerable")
        if self.planted != (self.planted_why is not None):
            raise ValueError("planted and planted_why must agree")
        return self


def load_items(path: Path = TESTSET, split: str | None = None) -> list[Item]:
    """The items in the file, optionally one split, sorted by id. Raises ValueError naming the line on a bad row."""
    items: list[Item] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append(Item.model_validate_json(line))
        except ValidationError as error:
            raise ValueError(f"line {number}: {error.error_count()} problem(s), first {error.errors(include_url=False)[0]['msg']}") from None
    if split is not None:
        items = [item for item in items if item.split == split]
    return sorted(items, key=lambda item: item.id)


# ---- checks added in chapter 3: every row, then the rules that look across items (plan sections 3.2 to 3.4) ----


def item_problems(path: Path = TESTSET) -> tuple[list[Item], list[str]]:
    """Every row validated, without stopping at the first bad one: the valid items, and one problem per bad row."""
    items: list[Item] = []
    problems: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append(Item.model_validate_json(line))
        except ValidationError as error:
            first = error.errors(include_url=False)[0]["msg"]
            problems.append(f"line {number}: {error.error_count()} problem(s), first {first}")
    return items, problems


def _words(text: str) -> list[str]:
    """The words of a text: whitespace-separated, outer punctuation stripped, lower case; "folder's" is one word."""
    return [word for word in (token.strip(".,;:!?()[]{}`'\"*_#-") for token in text.lower().split()) if word]


def cross_item_problems(items: list[Item]) -> list[str]:
    """The rules that look across items, as sorted problem strings; an empty list means the set passes.

    Covers unique ids, twins (named back, another version, both version-dependent, same split), supporting sections
    that exist in the docs, reference answers that copy no more than ten words of a section, the planted traps, and
    the stratification of plan section 3.4.
    """
    problems: list[str] = []
    by_id = {item.id: item for item in items}
    for item_id, count in Counter(item.id for item in items).items():
        if count > 1:
            problems.append(f"{item_id}: id used {count} times")
    for item in items:
        if item.twin_of is not None:
            twin = by_id.get(item.twin_of)
            if twin is None:
                problems.append(f"{item.id}: twin {item.twin_of} is not in the set")
            else:
                if twin.twin_of != item.id:
                    problems.append(f"{item.id}: twin {item.twin_of} does not name it back")
                if twin.version == item.version:
                    problems.append(f"{item.id}: twin {item.twin_of} asks the same version")
                if item.kind != "version-dependent" or twin.kind != "version-dependent":
                    problems.append(f"{item.id}: twins are both version-dependent")
                if twin.split != item.split:
                    problems.append(f"{item.id}: twin {item.twin_of} is in the other split")
        if item.planted_why == "false-premise" and item.kind != "unanswerable":
            problems.append(f"{item.id}: a false-premise item is unanswerable")
    known = {(version, section.section_id) for version in versions() for section in load_sections(version)}
    for item in items:
        for ref in item.supporting_sections:
            if (ref.version, ref.section_id) not in known:
                problems.append(f"{item.id}: section {ref.version}/{ref.section_id} is not in the docs")
    copied = set()  # every run of eleven words in every section of every version
    for version in versions():
        for section in load_sections(version):
            words = _words(section.title + " " + section.text)
            copied.update(tuple(words[i : i + 11]) for i in range(len(words) - 10))
    for item in items:
        words = _words(item.reference_answer or "")
        if any(tuple(words[i : i + 11]) in copied for i in range(len(words) - 10)):
            problems.append(f"{item.id}: reference copies more than ten words of a section")
    return sorted(problems) + split_problems(items)


def split_problems(items: list[Item]) -> list[str]:
    """Plan section 3.4: 120 items, dev 80 and held-out 40 by kind, planted items 16 and 8, twelve pairs and one
    singleton, and the chapter 1 set (q-0001 to q-0020, all dev, by kind and planted count)."""
    problems: list[str] = []
    if len(items) != 120:
        problems.append(f"the set holds {len(items)} items, want 120")
    want = {
        ("dev", "answerable"): 40, ("dev", "unanswerable"): 13, ("dev", "version-dependent"): 17, ("dev", "ambiguous"): 10,
        ("held-out", "answerable"): 20, ("held-out", "unanswerable"): 7, ("held-out", "version-dependent"): 8,
        ("held-out", "ambiguous"): 5,
    }
    counts = Counter((item.split, item.kind) for item in items)
    for (split, kind), n in want.items():
        if counts[(split, kind)] != n:
            problems.append(f"{split} {kind}: {counts[(split, kind)]} items, want {n}")
    planted = Counter(item.split for item in items if item.planted)
    if planted["dev"] != 16 or planted["held-out"] != 8:
        problems.append(f"planted items: dev {planted['dev']}, held-out {planted['held-out']}, want 16 and 8")
    versioned = [item for item in items if item.kind == "version-dependent"]
    pairs = {tuple(sorted((item.id, item.twin_of))) for item in versioned if item.twin_of}
    singles = [item.id for item in versioned if item.twin_of is None]
    if len(pairs) != 12 or len(singles) != 1:
        problems.append(f"version-dependent items: {len(pairs)} pairs and {len(singles)} singletons, want 12 and 1")
    chapter = [item for item in items if re.fullmatch(r"q-00(0[1-9]|1[0-9]|20)", item.id)]
    chapter_kinds = Counter(item.kind for item in chapter)
    if len(chapter) != 20 or any(item.split != "dev" for item in chapter):
        problems.append("the chapter 1 set is q-0001 to q-0020, all dev")
    for kind, n in {"answerable": 10, "unanswerable": 4, "version-dependent": 4, "ambiguous": 2}.items():
        if chapter_kinds[kind] != n:
            problems.append(f"chapter 1 set: {chapter_kinds[kind]} {kind} items, want {n}")
    if sum(item.planted for item in chapter) != 4:
        problems.append("chapter 1 set: planted items are not 4")
    return problems
