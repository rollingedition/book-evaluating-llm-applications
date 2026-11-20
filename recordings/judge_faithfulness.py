"""Records the faithfulness judge's verdicts on the answered items of assistant-baseline (plan sections 8.3 and 9).

    python recordings/judge_faithfulness.py              # judge-faithfulness-baseline, into examples/data/recorded/
    python recordings/judge_faithfulness.py --limit 2    # smoke: the first N answered items, scratch only

An answered item is one whose baseline reply is not the decline phrase and is not empty. The judge sees the sections
the assistant saw and the reply, and never the reference answer. Those sections are retrieved again with the baseline
settings (filtered to the item's version, k=3, bm25s) and must equal the sections the baseline recorded, or the run stops.
Temperature 0, seed 4217, max_tokens 160, thinking none (Qwen3-4B-Instruct-2507). Replies are raw, sorted by item.
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
from lib.contract import parse_reply  # noqa: E402
from lib.docs import Section, load_sections  # noqa: E402
from lib.prompts import FAITH_SHA256, faith_messages  # noqa: E402
from lib.replay import ReplayModel  # noqa: E402
from lib.retrieval import Retriever  # noqa: E402
from lib.testset import TESTSET, Item, load_items  # noqa: E402
from local_model import JUDGE_SAMPLING, QWEN4B, SEED, THREADS, LocalModel, describe  # noqa: E402
from recorded import RECORDED, Recording  # noqa: E402

SOURCE = "assistant-baseline"
NAME = "judge-faithfulness-baseline"
K = 3
VERDICT = re.compile(r"^VERDICT:\s*(SUPPORTED|UNSUPPORTED)$")
SCRATCH = Path.home() / "scratch" / "rec2" / "smoke"


def parse_faithfulness(raw: str) -> str | None:
    """'SUPPORTED' or 'UNSUPPORTED' from the reply's first non-empty line, else None."""
    lines = [line.strip().strip("*`").strip() for line in raw.splitlines() if line.strip()]
    match = VERDICT.match(lines[0]) if lines else None
    return match.group(1) if match else None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def answered_items() -> list[tuple[Item, str, list[Section]]]:
    """Each answered baseline item with its reply and the sections the assistant saw, checked against the recording."""
    source = ReplayModel(SOURCE)
    context = {}
    for line in (RECORDED / SOURCE / "replies.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        context[row["item"]] = row["context"]
    sections = load_sections()
    by_key = {(s.version, s.section_id): s for s in sections}
    retrievers: dict[str, Retriever] = {}
    out = []
    for item in load_items(TESTSET):
        reply = source.reply(item.id, 0)
        parsed = parse_reply(reply)
        if parsed.declined or not parsed.text:
            continue
        if item.version not in retrievers:
            retrievers[item.version] = Retriever([s for s in sections if s.version == item.version])
        hits = retrievers[item.version].retrieve(item.question, K)
        got = [f"{h.version}/{h.section_id}" for h in hits]
        if got != context[item.id]:
            raise SystemExit(f"retrieval for {item.id} does not match the sections {SOURCE} recorded")
        out.append((item, reply, [by_key[(h.version, h.section_id)] for h in hits]))
    return out


def smoke(count: int) -> None:
    """Judges the first N answered items, prints each verdict, and writes the raw replies to scratch only."""
    model = LocalModel(QWEN4B, JUDGE_SAMPLING)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    rows = []
    for item, reply, sections in answered_items()[:count]:
        judged = model.complete(faith_messages(sections, reply))
        rows.append({"item": item.id, "sample": 0, "reply": judged})
        print(f"{item.id}: verdict={parse_faithfulness(judged)}")
    (SCRATCH / f"{NAME}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                           encoding="utf-8")


def record() -> None:
    """The full recording, resumable, with the source recording named in the manifest by name and prompt hash."""
    source = ReplayModel(SOURCE)
    items = answered_items()
    manifest = describe(QWEN4B, JUDGE_SAMPLING)
    testset_path = TESTSET
    with Recording(NAME, model=QWEN4B.model, model_version=manifest["model_version"], prompt_sha256=FAITH_SHA256,
                   fresh=False, judge="judge-4b", criterion="faithfulness: every claim supported, VERDICT first",
                   judges={"recording": source.name, "prompt_sha256": source.prompt_sha256},
                   items=len(items), samples=1, tuned_on="nothing", depends_on=source.name,
                   retrieval="bm25s 0.3.16, BM25 k1=1.5 b=0.75, filtered to the item's version, k=3",
                   testset=testset_path.name, testset_sha256=sha256_file(testset_path),
                   settings=manifest, threads=THREADS, seed=SEED,
                   prompt_text="lib/prompts.py: FAITH_SYSTEM and FAITH_TEMPLATE") as out:
        partial = out / "replies.partial.jsonl"
        done: dict[str, str] = {}
        if partial.exists():
            for line in partial.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                done[row["item"]] = row["reply"]
        model = LocalModel(QWEN4B, JUDGE_SAMPLING)
        with partial.open("w", encoding="utf-8") as f:
            for item_id, reply in sorted(done.items()):
                f.write(json.dumps({"item": item_id, "sample": 0, "reply": reply}, ensure_ascii=False) + "\n")
            for item, reply, sections in items:
                if item.id in done:
                    continue
                judged = model.complete(faith_messages(sections, reply))
                f.write(json.dumps({"item": item.id, "sample": 0, "reply": judged}, ensure_ascii=False) + "\n")
                f.flush()
        final = sorted((json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()),
                       key=lambda r: (r["item"], r["sample"]))
        (out / "replies.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final),
                                           encoding="utf-8")
        partial.unlink()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--limit", type=int, default=0, help="smoke: judge the first N answered items into scratch")
    args = parser.parse_args(argv)
    if args.limit:
        smoke(args.limit)
    else:
        record()


if __name__ == "__main__":
    main()
