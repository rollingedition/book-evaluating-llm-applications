"""Loaders and scorers for the two benchmark samples (chapter 3): GSM8K by exact match on the final number, and
TruthfulQA MC1 by the option letter the reply gives.

A reply that can't be read is None, not wrong: scorers return it with verdict None, so a rate counts only the readable
replies and the unreadable ones are listed apart. Every returned list is sorted by item ID.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent.parent / "data"
GSM8K = DATA / "gsm8k" / "sample.jsonl"
TRUTHFULQA = DATA / "truthfulqa" / "mc1.jsonl"

# A number as GSM8K writes it: "1,200" or "540", optionally "540.0". A comma counts only inside a group of three digits,
# so "540, so" ends at 540.
NUMBER = r"-?[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|-?[0-9]+(?:\.[0-9]+)?"
HASH_NUMBER = re.compile(r"####\s*\$?(" + NUMBER + ")")
ANY_NUMBER = re.compile(NUMBER)
LETTER = re.compile(r"^\(?([A-Z])\)?(?:[.:)\s]|$)")


def normal_number(text: str) -> str:
    """A number as a string with its commas removed and a trailing .0 (or .00) dropped: "1,200.0" gives "1200"."""
    text = text.replace(",", "")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def load_gsm8k(path: Path = GSM8K) -> list[dict]:
    """The sample's rows sorted by id, each with its reference: the number on the answer's last '#### N' line."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        found = HASH_NUMBER.findall(row["answer"])
        if not found:
            raise ValueError(f"item {row['id']} has no '#### N' reference")
        rows.append({"id": row["id"], "question": row["question"], "reference": normal_number(found[-1])})
    return sorted(rows, key=lambda row: row["id"])


def load_truthfulqa(path: Path = TRUTHFULQA) -> list[dict]:
    """The sample's rows sorted by id, each with its correct option as a letter (the choices are lettered A, B, ...)."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows.append({"id": row["id"], "question": row["question"], "choices": row["choices"],
                     "correct": chr(65 + row["correct_index"])})
    return sorted(rows, key=lambda row: row["id"])


# The seed of the option shuffle. Each item draws its permutation from default_rng([SHUFFLE_SEED, k]), where k is a
# stable integer taken from the item's ID (the first four bytes of its SHA-256), so an item's order does not change
# when other items are added.
SHUFFLE_SEED = 1729


def shuffle_order(item_id: str, options: int) -> list[int]:
    """The original index of the option shown at each position, for one item: a seeded permutation of range(options)."""
    k = int.from_bytes(hashlib.sha256(item_id.encode("utf-8")).digest()[:4], "big")
    return [int(i) for i in np.random.default_rng([SHUFFLE_SEED, k]).permutation(options)]


def load_truthfulqa_shuffled(path: Path = TRUTHFULQA) -> list[dict]:
    """load_truthfulqa with each item's options permuted by shuffle_order. Each row keeps the same option texts; "choices"
    holds them in their new order, "correct" and "correct_index" give the correct option's new position, and "order"
    gives the original index at each position. Sorted by item ID."""
    rows = []
    for row in load_truthfulqa(path):
        original = row["choices"]
        order = shuffle_order(row["id"], len(original))
        correct_index = order.index(ord(row["correct"]) - 65)
        rows.append({"id": row["id"], "question": row["question"], "choices": [original[i] for i in order],
                     "correct": chr(65 + correct_index), "correct_index": correct_index, "order": order})
    return rows


def parse_gsm8k(reply: str) -> str | None:
    """The reply's final number: its last '#### N', or else its last number. None when the reply has no number."""
    found = HASH_NUMBER.findall(reply) or ANY_NUMBER.findall(reply)
    return normal_number(found[-1]) if found else None


def parse_tqa(reply: str, options: int) -> str | None:
    """The option letter on the reply's first non-empty line, as the prompt asks it (the letter alone). None when the
    line holds no letter or a letter past the last option."""
    lines = [line.strip().strip("*`").strip() for line in reply.splitlines() if line.strip()]
    if not lines:
        return None
    line = re.sub(r"^(answer|reply)\s*:\s*", "", lines[0], flags=re.IGNORECASE)
    match = LETTER.match(line)
    return match.group(1) if match and ord(match.group(1)) - 65 < options else None


def score_gsm8k(rows: list[dict], replies: dict[str, str]) -> list[tuple[str, str | None, bool | None]]:
    """(item ID, parsed number, verdict) for each row: verdict True or False, or None when the reply is unreadable."""
    scored = []
    for row in rows:
        parsed = parse_gsm8k(replies[row["id"]])
        scored.append((row["id"], parsed, None if parsed is None else parsed == row["reference"]))
    return sorted(scored, key=lambda entry: entry[0])


def score_truthfulqa(rows: list[dict], replies: dict[str, str]) -> list[tuple[str, str | None, bool | None]]:
    """(item ID, chosen letter, verdict) for each row: verdict True or False, or None when the reply is unreadable."""
    scored = []
    for row in rows:
        letter = parse_tqa(replies[row["id"]], len(row["choices"]))
        scored.append((row["id"], letter, None if letter is None else letter == row["correct"]))
    return sorted(scored, key=lambda entry: entry[0])
