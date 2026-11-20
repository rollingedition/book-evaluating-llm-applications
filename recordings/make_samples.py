"""Make the public data samples for Evaluating LLM Applications.

    python3 -I recordings/make_samples.py

Downloads each dataset at its pinned commit from huggingface.co into a cache under ~/scratch/data. Each download is
checked against the SHA-256 that the Hub lists for it (the LFS hash), and each card's licence is read from the README at
the same commit. Then it writes the samples under examples/data/ and a manifest beside them.

No model runs here, so this script does not use Recording. The output is byte-identical on every run, and the script
prints only counts. Needs numpy and pyarrow (the parquet files); neither is part of the examples' runtime.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import shutil
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow
import pyarrow.parquet as pq

BOOK = Path(__file__).resolve().parent.parent
DATA = BOOK / "examples" / "data"
CACHE = Path.home() / "scratch" / "data" / "downloads"
HUB = "https://huggingface.co"
READ_DATE = "2026-11-20"
SEED = 0

SOURCES = {
    "helpsteer2": {
        "repo": "nvidia/HelpSteer2",
        "commit": "990b2711a36180dd19d9c94b8627844866f8982a",
        "files": ["validation.jsonl.gz", "preference/preference.jsonl.gz"],
        "licence": "cc-by-4.0",
    },
    "gsm8k": {
        "repo": "openai/gsm8k",
        "commit": "740312add88f781978c0658806c59bc2815b9866",
        "files": ["main/test-00000-of-00001.parquet"],
        "licence": "mit",
    },
    "truthfulqa": {
        "repo": "truthfulqa/truthful_qa",
        "commit": "741b8276f2d1982aa3d5b832d3ee81ed3b896490",
        "files": ["multiple_choice/validation-00000-of-00001.parquet"],
        "licence": "apache-2.0",
    },
    # Cited only, nothing shipped (managing editor's decision). Read for its card and licence, not downloaded as data.
    "mt_bench_human_judgments": {
        "repo": "lmsys/mt_bench_human_judgments",
        "commit": "f7d2896d2cc5d80f8b55c2bbc722613555233c25",
        "files": [],
        "licence": "cc-by-4.0",
    },
}

ATTRIBUTES = ["helpfulness", "correctness", "coherence", "complexity", "verbosity"]
MAX_PROMPT_WORDS = 300
MAX_RESPONSE_WORDS = 400
PRINTABLE = re.compile(r"[\t\n\r\x20-\x7e]*")

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)(?:\+\d{1,3}[ .-]?)?(?:\(\d{2,4}\)[ .-]?|\d{2,4}[ .-])\d{3,4}[ .-]\d{3,4}(?!\d)")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,4})?\b")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")


# ---------- downloading and checking ----------

def fetch_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hub_entry(repo: str, commit: str, path: str) -> dict:
    parent = path.rsplit("/", 1)[0] if "/" in path else ""
    url = f"{HUB}/api/datasets/{repo}/tree/{commit}" + (f"/{parent}" if parent else "")
    for entry in json.loads(fetch_bytes(url)):
        if entry["path"] == path:
            return entry
    raise SystemExit(f"file not listed at the pinned commit: {repo} {path}")


def card_licence(text: str) -> str:
    match = re.search(r"^license:[ \t]*\n?(?:-[ \t]*)?([A-Za-z0-9.\-]+)", text, re.M)
    if not match:
        raise SystemExit("no licence in the card front matter")
    return match.group(1).lower()


def fetch_source(name: str, spec: dict) -> dict:
    repo, commit = spec["repo"], spec["commit"]
    card = fetch_bytes(f"{HUB}/datasets/{repo}/raw/{commit}/README.md")
    licence = card_licence(card.decode("utf-8"))
    if licence != spec["licence"]:
        raise SystemExit(f"{name}: card says {licence}, expected {spec['licence']}")
    record = {
        "card_licence": licence,
        "card_sha256": sha256_bytes(card),
        "card_url": f"{HUB}/datasets/{repo}/blob/{commit}/README.md",
        "commit": commit,
        "files": [],
        "repo": repo,
    }
    for path in spec["files"]:
        entry = hub_entry(repo, commit, path)
        if not entry.get("lfs"):
            raise SystemExit(f"{name}: {path} is not an LFS file at the pinned commit")
        expected = entry["lfs"]["oid"]
        local = CACHE / name / commit / path
        if not (local.exists() and sha256_file(local) == expected):
            local.parent.mkdir(parents=True, exist_ok=True)
            partial = local.with_name(local.name + ".part")
            partial.write_bytes(fetch_bytes(f"{HUB}/datasets/{repo}/resolve/{commit}/{path}"))
            partial.replace(local)
        digest = sha256_file(local)
        if digest != expected:
            raise SystemExit(f"{name}: {path} does not match the Hub's SHA-256")
        record["files"].append({
            "bytes": local.stat().st_size,
            "path": path,
            "sha256": digest,
            "url": f"{HUB}/datasets/{repo}/resolve/{commit}/{path}",
        })
    return record


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            yield index, json.loads(line)


# ---------- filters ----------

def ascii_printable(text: str) -> bool:
    return PRINTABLE.fullmatch(text) is not None


def words(text: str) -> int:
    return len(text.split())


def luhn(digits: str) -> bool:
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def iban_valid(compact: str) -> bool:
    if not 15 <= len(compact) <= 34:
        return False
    rearranged = compact[4:] + compact[:4]
    return int("".join(str(int(char, 36)) for char in rearranged)) % 97 == 1


def personal_data(text: str) -> str | None:
    """Return the kind of personal data found in the text, or None."""
    if EMAIL.search(text):
        return "email"
    for match in PHONE.finditer(text):
        if 10 <= sum(char.isdigit() for char in match.group()) <= 15:
            return "phone"
    for match in CARD.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if 13 <= len(digits) <= 19 and luhn(digits):
            return "card number"
    for match in IBAN.finditer(text):
        if iban_valid(match.group().replace(" ", "")):
            return "iban"
    if SSN.search(text):
        return "national id"
    return None


def pick(pool: list, size: int, rng: np.random.Generator) -> list:
    """Sample `size` items without replacement; the pool is already in stable order."""
    chosen = rng.choice(len(pool), size=size, replace=False)
    return [pool[int(i)] for i in sorted(chosen.tolist())]


# ---------- samples ----------

def build_ratings(path: Path, drops: Counter) -> list[dict]:
    """180 HelpSteer2 validation rows: 90 dev and 90 held-out, each split 45 PASS and 45 FAIL."""
    pool = {"PASS": [], "FAIL": []}
    seen_prompts: set[str] = set()
    for index, row in read_jsonl_gz(path):
        prompt, response = row["prompt"], row["response"]
        score = row["correctness"]
        if not (isinstance(score, int) and 0 <= score <= 4):
            drops["ratings: correctness not 0-4"] += 1
            continue
        if not (ascii_printable(prompt) and ascii_printable(response)):
            drops["ratings: not ASCII-printable"] += 1
            continue
        if words(prompt) > MAX_PROMPT_WORDS or words(response) > MAX_RESPONSE_WORDS:
            drops["ratings: over word limit"] += 1
            continue
        found = personal_data(prompt) or personal_data(response)
        if found:
            drops[f"ratings: {found}"] += 1
            continue
        if prompt in seen_prompts:
            drops["ratings: prompt already used"] += 1
            continue
        seen_prompts.add(prompt)
        pool["PASS" if score >= 3 else "FAIL"].append((index, row))

    # Each split takes 45 FAIL and 45 PASS where the pool allows. FAIL rows are scarce once each prompt is kept once,
    # so FAIL takes what the pool holds and PASS fills the rest of the 90 per split.
    fail_each = min(45, len(pool["FAIL"]) // 2)
    pass_each = 90 - fail_each
    rng = np.random.default_rng(SEED)
    chosen = []
    for label, each in (("FAIL", fail_each), ("PASS", pass_each)):
        stratum = pick(pool[label], 2 * each, rng)
        order = rng.permutation(len(stratum))
        for position, item in enumerate(order):
            split = "dev" if position < each else "held-out"
            chosen.append((stratum[int(item)][0], split, stratum[int(item)][1], label))

    rows = []
    for number, (index, split, row, label) in enumerate(sorted(chosen, key=lambda c: c[0]), start=1):
        record = {"id": f"hs2-{number:04d}", "prompt": row["prompt"], "response": row["response"]}
        record.update({name: row[name] for name in ATTRIBUTES})
        record["split"] = split
        rows.append(record)
    return rows


def build_pairs(path: Path, drops: Counter, ratings_split: dict[str, str]) -> list[dict]:
    """150 non-tie HelpSteer2 preference pairs from the validation split: 75 dev and 75 held-out.

    A prompt that also appears in the ratings file keeps its ratings split, so no prompt is dev in one file and
    held-out in the other. The remaining pairs are split by the seeded permutation to fill 75 dev and 75 held-out.
    """
    pool = []
    seen_prompts: set[str] = set()
    for index, row in read_jsonl_gz(path):
        if row["split"] != "val":  # the preference file labels its splits "train" and "val"
            continue
        strength = row["preference_strength"]
        if strength == 0:
            drops["pairs: tie"] += 1
            continue
        prompt, a, b = row["prompt"], row["response_1"], row["response_2"]
        if not all(ascii_printable(text) for text in (prompt, a, b)):
            drops["pairs: not ASCII-printable"] += 1
            continue
        if words(prompt) > MAX_PROMPT_WORDS or max(words(a), words(b)) > MAX_RESPONSE_WORDS:
            drops["pairs: over word limit"] += 1
            continue
        found = personal_data(prompt) or personal_data(a) or personal_data(b)
        if found:
            drops[f"pairs: {found}"] += 1
            continue
        if prompt in seen_prompts:
            drops["pairs: prompt already used"] += 1
            continue
        seen_prompts.add(prompt)
        pool.append((index, row))

    rng = np.random.default_rng(SEED)
    chosen = pick(pool, 150, rng)
    split_of: dict[int, str] = {}
    free = []
    for number, (index, row) in enumerate(chosen, start=1):
        if row["prompt"] in ratings_split:
            split_of[number - 1] = ratings_split[row["prompt"]]
        else:
            free.append(number - 1)
    need_dev = 75 - sum(1 for s in split_of.values() if s == "dev")
    need_held = 75 - sum(1 for s in split_of.values() if s == "held-out")
    if need_dev < 0 or need_held < 0 or need_dev + need_held != len(free):
        raise SystemExit("shared prompts' ratings splits do not leave 75 dev and 75 held-out pairs")
    order = rng.permutation(len(free))
    for position, item in enumerate(order):
        split_of[free[int(item)]] = "dev" if position < need_dev else "held-out"
    rows = []
    for number, (index, row) in enumerate(chosen, start=1):
        strength = row["preference_strength"]
        rows.append({
            "id": f"hs2-pref-{number:04d}",
            "preferred": "a" if strength < 0 else "b",
            "prompt": row["prompt"],
            "response_a": row["response_1"],
            "response_b": row["response_2"],
            "split": split_of[number - 1],
            "strength": abs(strength),
        })
    return rows


def build_gsm8k(path: Path, drops: Counter) -> list[dict]:
    """100 items of the main test split."""
    table = pq.read_table(path).to_pylist()
    pool = []
    for index, row in enumerate(table):
        found = personal_data(row["question"]) or personal_data(row["answer"])
        if found:
            drops[f"gsm8k: {found}"] += 1
            continue
        pool.append((index, row))
    rng = np.random.default_rng(SEED)
    rows = []
    for index, row in pick(pool, 100, rng):
        assert "####" in row["answer"]
        rows.append({
            "answer": row["answer"],
            "final_answer": row["answer"].rsplit("####", 1)[1].strip(),
            "id": f"gsm8k-test-{index:04d}",
            "question": row["question"],
        })
    return rows


def build_truthfulqa(path: Path, drops: Counter) -> list[dict]:
    """100 items of the multiple_choice validation split, MC1 targets only."""
    table = pq.read_table(path).to_pylist()
    pool = []
    for index, row in enumerate(table):
        targets = row["mc1_targets"]
        choices, labels = targets["choices"], targets["labels"]
        assert len(choices) == len(labels) and sum(labels) == 1
        found = personal_data(row["question"]) or personal_data("\n".join(choices))
        if found:
            drops[f"truthfulqa: {found}"] += 1
            continue
        pool.append((index, row, choices, labels))
    rng = np.random.default_rng(SEED)
    rows = []
    for index, row, choices, labels in pick(pool, 100, rng):
        rows.append({
            "choices": choices,
            "correct_index": labels.index(1),
            "id": f"truthfulqa-val-{index:04d}",
            "question": row["question"],
        })
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows)
    path.write_bytes(lines.encode("ascii"))
    return {"bytes": path.stat().st_size, "rows": len(rows), "sha256": sha256_bytes(path.read_bytes())}


def relative(path: Path) -> str:
    return path.relative_to(BOOK).as_posix()


def main() -> None:
    sources = {name: fetch_source(name, spec) for name, spec in sorted(SOURCES.items())}
    drops: Counter = Counter()
    hs = sources["helpsteer2"]["files"]
    hs_paths = {entry["path"]: CACHE / "helpsteer2" / SOURCES["helpsteer2"]["commit"] / entry["path"] for entry in hs}

    ratings = build_ratings(hs_paths["validation.jsonl.gz"], drops)
    pairs = build_pairs(hs_paths["preference/preference.jsonl.gz"], drops, {r["prompt"]: r["split"] for r in ratings})
    gsm_path = CACHE / "gsm8k" / SOURCES["gsm8k"]["commit"] / "main/test-00000-of-00001.parquet"
    tqa_path = CACHE / "truthfulqa" / SOURCES["truthfulqa"]["commit"] / "multiple_choice/validation-00000-of-00001.parquet"
    gsm = build_gsm8k(gsm_path, drops)
    tqa = build_truthfulqa(tqa_path, drops)

    outputs = {
        "helpsteer2/ratings.jsonl": ratings,
        "helpsteer2/preferences.jsonl": pairs,
        "gsm8k/sample.jsonl": gsm,
        "truthfulqa/mc1.jsonl": tqa,
    }
    files = []
    for name, rows in outputs.items():
        path = DATA / name
        info = write_jsonl(path, rows)
        files.append({"path": relative(path), **info})
        print(f"{name}: {info['rows']} rows")

    splits = {
        "ratings": Counter(r["split"] for r in ratings),
        "pairs": Counter(r["split"] for r in pairs),
    }
    balance = {
        "ratings_pass_fail": {
            "FAIL": sum(1 for r in ratings if r["correctness"] <= 2),
            "PASS": sum(1 for r in ratings if r["correctness"] >= 3),
        },
        "pairs_preferred": {
            "a": sum(1 for r in pairs if r["preferred"] == "a"),
            "b": sum(1 for r in pairs if r["preferred"] == "b"),
        },
    }
    print("ratings splits:", dict(sorted(splits["ratings"].items())), "PASS/FAIL:", balance["ratings_pass_fail"])
    print("pairs splits:", dict(sorted(splits["pairs"].items())), "preferred:", balance["pairs_preferred"])
    for key, count in sorted(drops.items()):
        print(f"dropped {key}: {count}")

    manifest = {
        "balance": balance,
        "dropped_before_sampling": dict(sorted(drops.items())),
        "files": sorted(files, key=lambda f: f["path"]),
        "filters": {
            "ascii_printable": "prompts and responses: tab, newline, carriage return and 0x20-0x7E only",
            "max_prompt_words": MAX_PROMPT_WORDS,
            "max_response_words": MAX_RESPONSE_WORDS,
            "personal_data": "email, phone, card number (Luhn), IBAN (mod 97), national id (NNN-NN-NNNN)",
            "unique_prompts": "first occurrence kept, so no prompt appears twice in a file",
        },
        "generator": {
            "script": relative(Path(__file__).resolve()),
            "numpy": np.__version__,
            "pyarrow": pyarrow.__version__,
            "read_date": READ_DATE,
            "seed": SEED,
            "sampling": "numpy.random.default_rng(SEED) per file; pools in source order; rng.choice without replacement",
        },
        "sources": {
            name: {
                "card_licence": record["card_licence"],
                "card_sha256": record["card_sha256"],
                "card_url": record["card_url"],
                "commit": record["commit"],
                "files": record["files"],
                "repo": record["repo"],
                "shipped": name != "mt_bench_human_judgments",
            }
            for name, record in sorted(sources.items())
        },
    }
    manifest_path = DATA / "manifest-samples.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
    print("manifest written")


if __name__ == "__main__":
    main()
