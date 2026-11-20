"""Loading the test set and the rules that look across items, from lib.testset, on rows written to a temporary file."""
import json

import pytest

import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.testset import TESTSET, Item, cross_item_problems, load_items


def _row(item_id, split="dev", kind="answerable", reference="Yes. The default writes the files."):
    return {
        "id": item_id,
        "question": "In sablefile 1.1, does a plain sync write the target files?",
        "version": "1.1",
        "kind": kind,
        "reference_answer": None if kind == "unanswerable" else reference,
        "supporting_sections": [] if kind == "unanswerable" else [{"version": "1.1", "section_id": "sync-default"}],
        "split": split,
        "planted": False,
        "planted_why": None,
        "twin_of": None,
    }


def _write(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_load_items_sorts_by_id_and_keeps_one_split(tmp_path):
    path = tmp_path / "set.jsonl"
    _write(path, [_row("q-0002", split="held-out"), _row("q-0001", split="dev")])
    assert [item.id for item in load_items(path)] == ["q-0001", "q-0002"]
    assert [item.id for item in load_items(path, split="dev")] == ["q-0001"]


def test_a_bad_row_is_named_by_its_line(tmp_path):
    path = tmp_path / "set.jsonl"
    bad = _row("q-0002", kind="unanswerable")
    bad["reference_answer"] = "Yes."  # an unanswerable item must have no reference answer
    _write(path, [_row("q-0001"), bad])
    with pytest.raises(ValueError, match="line 2"):
        load_items(path)


def test_an_item_needs_a_supporting_section_unless_it_is_unanswerable(tmp_path):
    row = _row("q-0001")
    row["supporting_sections"] = []
    with pytest.raises(ValueError):
        Item.model_validate(row)


def test_a_repeated_id_is_a_cross_item_problem(tmp_path):
    items = [Item.model_validate(_row("q-0001")), Item.model_validate(_row("q-0001"))]
    assert any("used 2 times" in problem for problem in cross_item_problems(items))


def test_the_book_test_set_has_eighty_dev_and_forty_held_out_items():
    items = load_items(TESTSET)
    assert len(items) == 120
    assert sum(item.split == "dev" for item in items) == 80
