"""Records the 4B model's replies on the two public benchmark samples (plan section 8.3).

    python recordings/bench.py --set gsm8k         # bench-gsm8k: examples/data/gsm8k/sample.jsonl, 100 items
    python recordings/bench.py --set truthfulqa    # bench-truthfulqa: examples/data/truthfulqa/mc1.jsonl, 100 items
    python recordings/bench.py --set truthfulqa-shuffled  # bench-truthfulqa-shuffled: the same items, options permuted
    python recordings/bench.py --set gsm8k --limit 2   # smoke: the first N items, scratch only, nothing in the book

GSM8K: a short chain of thought, then the final answer on a line of its own, "Final answer: N" (max 256 tokens).
TruthfulQA (MC1): the option letter alone (max 160 tokens). Both at temperature 0, seed 4217, thinking none
(Qwen3-4B-Instruct-2507). The prompts' examples are made up and use no item of either sample. Replies are raw, sorted
by item; scoring reads the replies with parse_gsm8k and parse_tqa, which are defined here and checked by --limit.
truthfulqa-shuffled gives each item its options in a seeded random order (lib.bench.SHUFFLE_SEED, written to the
manifest); the correct letter is then no longer always A.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
sys.path.insert(0, str(BOOK / "examples"))
sys.path.insert(0, str(HERE))

import lib  # noqa: E402  (first: fixes threads and seeds before any numerical library loads)
from lib.bench import SHUFFLE_SEED, load_truthfulqa_shuffled  # noqa: E402
from lib.prompts import (BENCH_GSM8K_SHA256, BENCH_TQA_SHA256, bench_gsm8k_messages,  # noqa: E402
                         bench_tqa_messages)
from local_model import ANSWER_SAMPLING, QWEN4B, SEED, THREADS, LocalModel, describe  # noqa: E402
from recorded import Recording  # noqa: E402

GSM8K_SAMPLING = {"temperature": 0.0, "max_tokens": 256}
FINAL = re.compile(r"Final answer:\s*\$?(-?[0-9][0-9,]*(?:\.[0-9]+)?)", re.IGNORECASE)
LETTER = re.compile(r"^\(?([A-Z])\)?(?:[.:)\s]|$)")
SETS = {
    "gsm8k": {"file": "examples/data/gsm8k/sample.jsonl", "name": "bench-gsm8k", "sha": BENCH_GSM8K_SHA256,
              "sampling": GSM8K_SAMPLING},
    "truthfulqa": {"file": "examples/data/truthfulqa/mc1.jsonl", "name": "bench-truthfulqa", "sha": BENCH_TQA_SHA256,
                   "sampling": ANSWER_SAMPLING},
    "truthfulqa-shuffled": {"file": "examples/data/truthfulqa/mc1.jsonl", "name": "bench-truthfulqa-shuffled",
                            "sha": BENCH_TQA_SHA256, "sampling": ANSWER_SAMPLING, "shuffled": True},
}
SCRATCH = Path.home() / "scratch" / "rec2" / "smoke"


def parse_gsm8k(raw: str) -> str | None:
    """The number on the last 'Final answer:' line, commas removed; None when the reply has no such line."""
    found = FINAL.findall(raw)
    return found[-1].replace(",", "") if found else None


def parse_tqa(raw: str, options: int) -> str | None:
    """The option letter on the reply's first non-empty line, if it is one of the options; else None."""
    lines = [line.strip().strip("*`").strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None
    line = re.sub(r"^(answer|reply)\s*:\s*", "", lines[0], flags=re.IGNORECASE)
    match = LETTER.match(line)
    return match.group(1) if match and ord(match.group(1)) - 65 < options else None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> list[dict]:
    """The sample's rows, sorted by id. Checks the count (100) and that ids are unique. A shuffled set's rows have
    their options permuted by lib.bench.load_truthfulqa_shuffled."""
    if SETS[name].get("shuffled"):
        rows = load_truthfulqa_shuffled(BOOK / SETS[name]["file"])
    else:
        rows = sorted((json.loads(line) for line in (BOOK / SETS[name]["file"]).read_text(encoding="utf-8").splitlines()
                       if line.strip()), key=lambda r: r["id"])
    if len(rows) != 100 or len({r["id"] for r in rows}) != 100:
        raise SystemExit(f"expected 100 items with unique ids, found {len(rows)}")
    return rows


def messages(name: str, row: dict) -> list[dict[str, str]]:
    if name == "gsm8k":
        return bench_gsm8k_messages(row["question"])
    return bench_tqa_messages(row["question"], row["choices"])


def reply_of(model: LocalModel, name: str, row: dict) -> str:
    return model.complete(messages(name, row))


def smoke(name: str, count: int) -> None:
    """Answers the first N items, prints the parsed answer against the expected one, and writes scratch only."""
    config = SETS[name]
    model = LocalModel(QWEN4B, config["sampling"])
    SCRATCH.mkdir(parents=True, exist_ok=True)
    rows = []
    for row in load(name)[:count]:
        reply = reply_of(model, name, row)
        rows.append({"item": row["id"], "sample": 0, "reply": reply})
        if name == "gsm8k":
            print(f"{row['id']}: parsed={parse_gsm8k(reply)} expected={row['final_answer']}")
        else:
            print(f"{row['id']}: parsed={parse_tqa(reply, len(row['choices']))} "
                  f"expected={chr(65 + row['correct_index'])}")
    (SCRATCH / f"{config['name']}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                                     encoding="utf-8")


def record(name: str) -> None:
    """The full recording, resumable: items answered so far are kept in the scratch folder and not answered again."""
    config = SETS[name]
    rows = load(name)
    manifest = describe(QWEN4B, config["sampling"])
    prompt_text = ("lib/prompts.py: BENCH_GSM8K_SYSTEM and BENCH_GSM8K_TEMPLATE" if name == "gsm8k"
                   else "lib/prompts.py: BENCH_TQA_SYSTEM and BENCH_TQA_TEMPLATE")
    shuffle = {"shuffle_seed": SHUFFLE_SEED} if config.get("shuffled") else {}
    if config.get("shuffled"):
        prompt_text += "; options permuted by lib/bench.py load_truthfulqa_shuffled"
    with Recording(config["name"], model=QWEN4B.model, model_version=manifest["model_version"],
                   prompt_sha256=config["sha"], fresh=False, bench=name, items=len(rows), samples=1,
                   tuned_on="nothing", data=config["file"], data_sha256=sha256_file(BOOK / config["file"]),
                   settings=manifest, threads=THREADS, seed=SEED, prompt_text=prompt_text, **shuffle) as out:
        partial = out / "replies.partial.jsonl"
        done: dict[str, str] = {}
        if partial.exists():
            for line in partial.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a line cut short when the run stopped; its item is answered again
                done[row["item"]] = row["reply"]
        model = LocalModel(QWEN4B, config["sampling"])
        with partial.open("w", encoding="utf-8") as f:
            for item, reply in sorted(done.items()):
                f.write(json.dumps({"item": item, "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
            for row in rows:
                if row["id"] in done:
                    continue
                reply = reply_of(model, name, row)
                f.write(json.dumps({"item": row["id"], "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
                f.flush()
        final = sorted((json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()),
                       key=lambda r: (r["item"], r["sample"]))
        (out / "replies.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final),
                                           encoding="utf-8")
        partial.unlink()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--set", required=True, choices=sorted(SETS))
    parser.add_argument("--limit", type=int, default=0, help="smoke: answer the first N items into scratch")
    args = parser.parse_args(argv)
    if args.limit:
        smoke(args.set, args.limit)
    else:
        record(args.set)


if __name__ == "__main__":
    main()
