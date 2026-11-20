"""Records the judge's replies on the 90 dev rows of the HelpSteer2 ratings, under a second wording of the rubric (plan 8.3).

    python recordings/judge_helpsteer2_rubric_b.py            # judge-helpsteer2-rubric-b, into examples/data/recorded/
    python recordings/judge_helpsteer2_rubric_b.py --limit 2  # smoke: the first N dev rows, scratch only

Dev rows only: the held-out rows are never judged under this wording. The wording is settled before recording and
tuned on nothing (tuned_on "nothing"). The judge sees the request and the response, and never the human score.
Temperature 0, seed 4217, max_tokens 160, thinking none (Qwen3-4B-Instruct-2507). Replies are raw, sorted by id.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
sys.path.insert(0, str(BOOK / "examples"))
sys.path.insert(0, str(HERE))

import lib  # noqa: E402  (first: fixes threads and seeds before any numerical library loads)
from lib.contract import parse_verdict  # noqa: E402
from lib.prompts import HS2B_SHA256, hs2b_messages  # noqa: E402
from local_model import JUDGE_SAMPLING, QWEN4B, SEED, THREADS, LocalModel, describe  # noqa: E402
from recorded import Recording  # noqa: E402

DATA = BOOK / "examples" / "data" / "helpsteer2" / "ratings.jsonl"
NAME = "judge-helpsteer2-rubric-b"
SCRATCH = Path.home() / "scratch" / "rec2" / "smoke"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dev_rows() -> list[dict]:
    """The dev rows of the ratings file, sorted by id. Checks that there are 90 and that ids are unique."""
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    dev = sorted((r for r in rows if r["split"] == "dev"), key=lambda r: r["id"])
    if len(dev) != 90 or len({r["id"] for r in dev}) != 90:
        raise SystemExit(f"expected 90 dev rows with unique ids, found {len(dev)}")
    return dev


def smoke(count: int) -> None:
    """Judges the first N dev rows, prints each verdict, and writes the raw replies to scratch only."""
    model = LocalModel(QWEN4B, JUDGE_SAMPLING)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    rows = []
    for row in load_dev_rows()[:count]:
        reply = model.complete(hs2b_messages(row["prompt"], row["response"]))
        rows.append({"item": row["id"], "sample": 0, "reply": reply})
        print(f"{row['id']}: verdict={parse_verdict(reply)}")
    (SCRATCH / f"{NAME}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                           encoding="utf-8")


def record() -> None:
    """The full recording, resumable: rows judged so far are kept in the scratch folder and not judged again."""
    rows = load_dev_rows()
    manifest = describe(QWEN4B, JUDGE_SAMPLING)
    with Recording(NAME, model=QWEN4B.model, model_version=manifest["model_version"], prompt_sha256=HS2B_SHA256,
                   fresh=False, judge="judge-4b", criterion="correctness, reference-free, second wording, PASS or FAIL",
                   items=len(rows), samples=1, tuned_on="nothing", split="dev",
                   data="examples/data/helpsteer2/ratings.jsonl", data_sha256=sha256_file(DATA),
                   settings=manifest, threads=THREADS, seed=SEED,
                   prompt_text="lib/prompts.py: HS2B_SYSTEM and HS2B_TEMPLATE") as out:
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
                reply = model.complete(hs2b_messages(row["prompt"], row["response"]))
                f.write(json.dumps({"item": row["id"], "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
                f.flush()
        final = sorted((json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()),
                       key=lambda r: (r["item"], r["sample"]))
        (out / "replies.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final),
                                           encoding="utf-8")
        partial.unlink()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--limit", type=int, default=0, help="smoke: judge the first N dev rows into scratch")
    args = parser.parse_args(argv)
    if args.limit:
        smoke(args.limit)
    else:
        record()


if __name__ == "__main__":
    main()
