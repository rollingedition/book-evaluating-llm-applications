"""Records the pairwise judge's verdicts on the 150 HelpSteer2 preference pairs (plan section 8.3).

    python recordings/judge_pairs.py --order ab              # judge-hs2-pairs-ab, into examples/data/recorded/
    python recordings/judge_pairs.py --order ba              # judge-hs2-pairs-ba: the two responses swapped
    python recordings/judge_pairs.py --order ab --limit 2    # smoke: the first N pairs, scratch only, nothing in the book

Order ab shows response_a as Response A. Order ba shows response_b as Response A, which measures position bias.
The judge sees the request and the two responses, and never the human preference. Temperature 0, seed 4217,
max_tokens 160, thinking none (Qwen3-4B-Instruct-2507). Replies are raw, one row per pair id, sorted by id.
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
from lib.prompts import PAIR_SHA256, pair_messages  # noqa: E402
from local_model import JUDGE_SAMPLING, QWEN4B, SEED, THREADS, LocalModel, describe  # noqa: E402
from recorded import Recording  # noqa: E402

DATA = BOOK / "examples" / "data" / "helpsteer2" / "preferences.jsonl"
SCRATCH = Path.home() / "scratch" / "rec2" / "smoke"
VERDICT = re.compile(r"^VERDICT:\s*(A|B)$")


def parse_pair(raw: str) -> str | None:
    """'A' or 'B' from the reply's first non-empty line (asterisks and backticks ignored), else None."""
    lines = [line.strip().strip("*`").strip() for line in raw.splitlines() if line.strip()]
    match = VERDICT.match(lines[0]) if lines else None
    return match.group(1) if match else None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows() -> list[dict]:
    """The 150 pairs, sorted by id. Checks the count and that ids are unique."""
    rows = sorted((json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()),
                  key=lambda r: r["id"])
    if len(rows) != 150 or len({r["id"] for r in rows}) != 150:
        raise SystemExit(f"expected 150 pairs with unique ids, found {len(rows)}")
    return rows


def shown(row: dict, order: str) -> tuple[str, str]:
    """The (Response A, Response B) pair the judge sees, for this order."""
    if order == "ab":
        return row["response_a"], row["response_b"]
    return row["response_b"], row["response_a"]


def smoke(order: str, count: int) -> None:
    """Runs the first pairs, prints each parsed verdict, and writes the raw replies to scratch only."""
    model = LocalModel(QWEN4B, JUDGE_SAMPLING)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    out = []
    for row in load_rows()[:count]:
        first, second = shown(row, order)
        reply = model.complete(pair_messages(row["prompt"], first, second))
        out.append({"item": row["id"], "sample": 0, "reply": reply})
        print(f"{row['id']}: verdict={parse_pair(reply)}")
    (SCRATCH / f"pairs-{order}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")


def record(order: str) -> None:
    """The full recording, resumable: pairs judged so far are kept in the scratch folder and not judged again."""
    rows = load_rows()
    manifest = describe(QWEN4B, JUDGE_SAMPLING)
    name = f"judge-hs2-pairs-{order}"
    with Recording(name, model=QWEN4B.model, model_version=manifest["model_version"], prompt_sha256=PAIR_SHA256,
                   fresh=False, judge="judge-4b", criterion="pairwise, VERDICT: A or B, verdict first",
                   order=order, presented=("response_a as A, response_b as B" if order == "ab"
                                           else "response_b as A, response_a as B"),
                   items=len(rows), samples=1, tuned_on="nothing", depends_on="none (judges the data file only)",
                   data="examples/data/helpsteer2/preferences.jsonl", data_sha256=sha256_file(DATA),
                   settings=manifest, threads=THREADS, seed=SEED,
                   prompt_text="lib/prompts.py: PAIR_SYSTEM and PAIR_TEMPLATE") as out:
        partial = out / "replies.partial.jsonl"
        done: dict[str, str] = {}
        if partial.exists():
            for line in partial.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a line cut short when the run stopped; its pair is judged again
                done[row["item"]] = row["reply"]
        model = LocalModel(QWEN4B, JUDGE_SAMPLING)
        with partial.open("w", encoding="utf-8") as f:
            for item, reply in sorted(done.items()):
                f.write(json.dumps({"item": item, "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
            for row in rows:
                if row["id"] in done:
                    continue
                first, second = shown(row, order)
                reply = model.complete(pair_messages(row["prompt"], first, second))
                f.write(json.dumps({"item": row["id"], "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
                f.flush()
        final = sorted((json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()),
                       key=lambda r: (r["item"], r["sample"]))
        (out / "replies.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final),
                                           encoding="utf-8")
        partial.unlink()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--order", required=True, choices=("ab", "ba"))
    parser.add_argument("--limit", type=int, default=0, help="smoke: judge the first N pairs into scratch only")
    args = parser.parse_args(argv)
    if args.limit:
        smoke(args.order, args.limit)
    else:
        record(args.order)


if __name__ == "__main__":
    main()
