"""Records one assistant variant over the test set (plan section 8.3). Not run yet: the test set is not final.

    python recordings/assistant.py --variant baseline    # examples/data/recorded/assistant-baseline/
    variants: baseline | prompt-b | k5 | unfiltered | second-model | variance

Every variant except `variance` answers all items once, at temperature 0 with seed 4217. `variance` answers the
dev items five times each, at temperature 0.7 (top-p 0.8, top-k 20), with seeds 1 to 5; each sample is keyed by its seed.
Rows are {"item", "sample", "reply", "context"}: the raw reply, and the sections in the prompt in rank order as
"version/section_id". Partial rows go to the recording's scratch folder as they arrive, so a run can be resumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
sys.path.insert(0, str(BOOK / "examples"))
sys.path.insert(0, str(HERE))

import lib  # noqa: E402  (first: fixes threads and seeds before any numerical library loads)
from lib.docs import Section, load_sections  # noqa: E402
from lib.prompts import P1_SHA256, P1_SYSTEM, P2_SHA256, P2_SYSTEM, answer_messages  # noqa: E402
from lib.retrieval import Retriever  # noqa: E402
from lib.testset import TESTSET, Item, load_items  # noqa: E402
from local_model import (ANSWER_SAMPLING, QWEN06B, QWEN4B, SEED, THREADS, VARIANCE_SAMPLING,  # noqa: E402
                         LocalModel, Pin, describe)
from recorded import Recording  # noqa: E402

RETRIEVAL = "bm25s 0.3.16, BM25 k1=1.5 b=0.75, stopwords en, ranked by (-score, section_id, version)"


@dataclass(frozen=True)
class Variant:
    """One assistant variant: its prompt, retrieval, model, sampling and the (sample, seed) runs per item."""

    name: str
    system: str
    system_sha256: str
    show_version: bool
    k: int
    filtered: bool
    pin: Pin
    sampling: dict
    runs: tuple[tuple[int, int], ...]
    dev_only: bool


SINGLE = ((0, SEED),)
VARIANCE_RUNS = tuple((seed, seed) for seed in (1, 2, 3, 4, 5))
VARIANTS = {
    "baseline": Variant("baseline", P1_SYSTEM, P1_SHA256, False, 3, True, QWEN4B, ANSWER_SAMPLING, SINGLE, False),
    "prompt-b": Variant("prompt-b", P2_SYSTEM, P2_SHA256, False, 3, True, QWEN4B, ANSWER_SAMPLING, SINGLE, False),
    "k5": Variant("k5", P1_SYSTEM, P1_SHA256, False, 5, True, QWEN4B, ANSWER_SAMPLING, SINGLE, False),
    "unfiltered": Variant("unfiltered", P1_SYSTEM, P1_SHA256, True, 3, False, QWEN4B, ANSWER_SAMPLING, SINGLE, False),
    "second-model": Variant("second-model", P1_SYSTEM, P1_SHA256, False, 3, True, QWEN06B, ANSWER_SAMPLING, SINGLE,
                            False),
    "variance": Variant("variance", P1_SYSTEM, P1_SHA256, False, 3, True, QWEN4B, VARIANCE_SAMPLING, VARIANCE_RUNS,
                        True),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_partial(path: Path) -> dict[tuple[str, int], dict]:
    """Rows already written by an earlier run. A line cut short when that run stopped is dropped and judged again."""
    done: dict[tuple[str, int], dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            done[(row["item"], row["sample"])] = row
    return done


def record(variant: Variant, testset: Path) -> None:
    """Answers every (item, run) pair not yet recorded, then writes the sorted replies and one manifest."""
    items: list[Item] = load_items(testset)
    if variant.dev_only:
        items = [item for item in items if item.split == "dev"]
    sections = load_sections()
    by_key: dict[tuple[str, str], Section] = {(s.version, s.section_id): s for s in sections}
    retrievers: dict[str, Retriever] = {}

    def retriever_for(item: Item) -> Retriever:
        key = item.version if variant.filtered else "all"
        if key not in retrievers:
            scope = [s for s in sections if s.version == item.version] if variant.filtered else sections
            retrievers[key] = Retriever(scope)
        return retrievers[key]

    manifest = describe(variant.pin, variant.sampling)
    with Recording(f"assistant-{variant.name}", model=variant.pin.model, model_version=manifest["model_version"],
                   prompt_sha256=variant.system_sha256, fresh=False, variant=variant.name, items=len(items),
                   runs=len(variant.runs), k=variant.k, filtered=variant.filtered,
                   show_version=variant.show_version, retrieval=RETRIEVAL, settings=manifest,
                   testset=testset.name, testset_sha256=sha256_file(testset), tuned_on="nothing",
                   threads=THREADS) as out:
        partial = out / "replies.partial.jsonl"
        done = read_partial(partial)
        model = LocalModel(variant.pin, variant.sampling)
        with partial.open("w", encoding="utf-8") as f:
            for row in sorted(done.values(), key=lambda r: (r["item"], r["sample"])):
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            for item in items:
                hits = retriever_for(item).retrieve(item.question, variant.k)
                shown = [by_key[(h.version, h.section_id)] for h in hits]
                messages = answer_messages(variant.system, item.question, shown, variant.show_version)
                for sample, seed in variant.runs:
                    if (item.id, sample) in done:
                        continue
                    reply = model.complete(messages, seed=seed)
                    row = {"item": item.id, "sample": sample, "reply": reply,
                           "context": [f"{h.version}/{h.section_id}" for h in hits]}
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
        rows = sorted((json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()),
                      key=lambda r: (r["item"], r["sample"]))
        (out / "replies.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                           encoding="utf-8")
        partial.unlink()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--variant", required=True, choices=sorted(VARIANTS))
    parser.add_argument("--testset", type=Path, default=TESTSET, help="the test set file (default: the book's)")
    args = parser.parse_args(argv)
    record(VARIANTS[args.variant], args.testset)


if __name__ == "__main__":
    main()
