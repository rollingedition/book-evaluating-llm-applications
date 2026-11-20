"""Records the judge's raw replies on the 180 HelpSteer2 rows: the calibration set for the reference-free judge.

    python recordings/judge_helpsteer2.py            # the full recording, into examples/data/recorded/judge-helpsteer2/
    python recordings/judge_helpsteer2.py --smoke 3  # the first N rows, printed; nothing is copied into the book

The judge sees the request and the response, and nothing else: never the human score. Temperature 0, seed 4217,
max_tokens 160, thinking none (Qwen3-4B-Instruct-2507). Replies are stored raw, one row per row id, sorted by id.
Partial replies go to the recording's scratch folder as they arrive, so a run that stops can be started again.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
sys.path.insert(0, str(BOOK / "examples"))
sys.path.insert(0, str(HERE))

import lib  # noqa: E402  (first: fixes threads and seeds before any numerical library loads)
from lib.contract import parse_verdict  # noqa: E402
from lib.prompts import HS2_SHA256, hs2_messages  # noqa: E402
from local_model import JUDGE_SAMPLING, QWEN4B, SEED, THREADS, LocalModel, describe  # noqa: E402
from recorded import Recording  # noqa: E402

DATA = BOOK / "examples" / "data" / "helpsteer2" / "ratings.jsonl"
NAME = "judge-helpsteer2"


def load_rows() -> list[dict]:
    """The 180 rows, sorted by id. Checks the count and that ids are unique."""
    rows = sorted((json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()),
                  key=lambda r: r["id"])
    if len(rows) != 180 or len({r["id"] for r in rows}) != 180:
        raise SystemExit(f"expected 180 rows with unique ids, found {len(rows)}")
    return rows


def sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoke(count: int) -> None:
    """Runs the first rows and prints each verdict. Writes nothing into the book."""
    model = LocalModel(QWEN4B, JUDGE_SAMPLING)
    for row in load_rows()[:count]:
        reply = model.complete(hs2_messages(row["prompt"], row["response"]))
        print(f"{row['id']}: verdict={parse_verdict(reply)}")
        print(reply)
        print("---")


def record() -> None:
    """The full recording, resumable. Replies are written sorted by id, with one manifest."""
    rows = load_rows()
    manifest_settings = describe(QWEN4B, JUDGE_SAMPLING)
    with Recording(NAME, model=QWEN4B.model, model_version=manifest_settings["model_version"],
                   prompt_sha256=HS2_SHA256, fresh=False,
                   judge="judge-4b", criterion="correctness, reference-free, PASS or FAIL",
                   items=len(rows), samples=1, tuned_on="nothing",
                   data="examples/data/helpsteer2/ratings.jsonl", data_sha256=sha256_file(DATA),
                   settings=manifest_settings, threads=THREADS, seed=SEED,
                   prompt_text="lib/prompts.py: HS2_SYSTEM and HS2_TEMPLATE") as out:
        partial = out / "replies.partial.jsonl"
        done: dict[str, str] = {}
        if partial.exists():
            for line in partial.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a line cut short when the run stopped; its row is judged again
                done[row["item"]] = row["reply"]
        model = LocalModel(QWEN4B, JUDGE_SAMPLING)
        with partial.open("w", encoding="utf-8") as f:
            for item, reply in sorted(done.items()):
                f.write(json.dumps({"item": item, "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
            for row in rows:
                if row["id"] in done:
                    continue
                reply = model.complete(hs2_messages(row["prompt"], row["response"]))
                f.write(json.dumps({"item": row["id"], "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
                f.flush()
        final = [json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()]
        final.sort(key=lambda r: (r["item"], r["sample"]))
        (out / "replies.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final), encoding="utf-8")
        partial.unlink()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--smoke", type=int, default=0, help="print the first N rows and record nothing")
    args = parser.parse_args(argv)
    if args.smoke:
        smoke(args.smoke)
    else:
        record()


if __name__ == "__main__":
    main()
