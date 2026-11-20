"""Records the reference-guided judge's verdicts on one assistant recording (plan section 8.3).

    python recordings/judge_answers.py --answers baseline    # reads assistant-baseline, writes judge-answers-baseline
    python recordings/judge_answers.py --answers variance    # reads assistant-variance, writes judge-answers-variance

The judge sees the question, the written reference answer (or "none" for an unanswerable item) and the reply, and
returns PASS or FAIL on the last line (lib/prompts.py: REF_SYSTEM). Every item is judged, declines included: a
correct decline on an unanswerable item is a PASS. Temperature 0, seed 4217, max_tokens 160.

Every answer recording except `variance` has one sample, 0. `variance` has the 60 dev items times samples 1 to 5
(the seeds of assistant.py); each verdict keeps the sample number of the reply it judges. `variance` refuses to start
until examples/data/recorded/assistant-variance/ is in the book, so it never judges a partial recording.

The judge's manifest names the answer recording it judges, by name and prompt_sha256, read from that recording's
manifest. Replies are raw text, one row per (item, sample), sorted by item and sample.
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
from lib.prompts import REF_SHA256, ref_messages  # noqa: E402
from lib.replay import RECORDED, ReplayModel  # noqa: E402
from lib.testset import TESTSET, load_items  # noqa: E402
from local_model import JUDGE_SAMPLING, QWEN4B, SEED, THREADS, LocalModel, describe  # noqa: E402
from recorded import Recording  # noqa: E402

ANSWER_RECORDINGS = ("baseline", "prompt-b", "k5", "unfiltered", "second-model", "variance")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(answers: str, testset: Path) -> None:
    """Judges every (item, sample) of the answer recording, resumably, then writes the sorted verdict replies."""
    if answers == "variance":
        folder = RECORDED / "assistant-variance"
        if not all((folder / name).is_file() for name in ("manifest.json", "replies.jsonl")):
            raise SystemExit(f"{folder} is not in the book yet: judge-answers-variance waits for the finished "
                             "assistant-variance recording, and never judges a partial one")
    source = ReplayModel(f"assistant-{answers}")
    items = load_items(testset)
    if answers == "variance":
        by_id = {item.id: item for item in items}
        pairs = [(by_id[item_id], sample) for item_id, sample in source.keys()]
    else:
        pairs = [(item, 0) for item in items]
    manifest = describe(QWEN4B, JUDGE_SAMPLING)
    with Recording(f"judge-answers-{answers}", model=QWEN4B.model, model_version=manifest["model_version"],
                   prompt_sha256=REF_SHA256, fresh=False, judge="judge-4b", criterion="reference-guided, PASS or FAIL",
                   judges={"recording": source.name, "prompt_sha256": source.prompt_sha256},
                   items=len({item.id for item, _ in pairs}), samples=len({s for _, s in pairs}),
                   tuned_on="nothing", testset=testset.name,
                   testset_sha256=sha256_file(testset), settings=manifest, threads=THREADS, seed=SEED) as out:
        partial = out / "replies.partial.jsonl"
        done: dict[tuple[str, int], str] = {}
        if partial.exists():
            for line in partial.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                done[(row["item"], row["sample"])] = row["reply"]
        model = LocalModel(QWEN4B, JUDGE_SAMPLING)
        with partial.open("w", encoding="utf-8") as f:
            for (item_id, sample), reply in sorted(done.items()):
                f.write(json.dumps({"item": item_id, "sample": sample, "reply": reply}, ensure_ascii=False) + "\n")
            for item, sample in pairs:
                if (item.id, sample) in done:
                    continue
                answer = source.reply(item.id, sample)
                reply = model.complete(ref_messages(item.question, item.reference_answer, answer))
                f.write(json.dumps({"item": item.id, "sample": sample, "reply": reply}, ensure_ascii=False) + "\n")
                f.flush()
        rows = sorted((json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()),
                      key=lambda r: (r["item"], r["sample"]))
        (out / "replies.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                           encoding="utf-8")
        partial.unlink()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--answers", required=True, choices=ANSWER_RECORDINGS)
    parser.add_argument("--testset", type=Path, default=TESTSET, help="the test set file (default: the book's)")
    args = parser.parse_args(argv)
    record(args.answers, args.testset)


if __name__ == "__main__":
    main()
