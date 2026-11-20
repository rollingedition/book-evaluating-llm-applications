"""ReplayModel: the recorded replies of one recording, read back as the same strings.

A recording is a folder under examples/data/recorded/NAME/ with manifest.json and replies.jsonl. Each row is
{"item": ID, "sample": N, "reply": TEXT}, sorted by (item, sample). A lookup is by (item, sample). A miss raises
KeyError naming the recording and the key; the model never falls back to another item.
"""
from __future__ import annotations

import json
from pathlib import Path

RECORDED = Path(__file__).resolve().parent.parent / "data" / "recorded"


class ReplayModel:
    """The replies of one recording. `prompt_sha256`, when given, must equal the manifest's, or loading fails."""

    def __init__(self, recording: str, prompt_sha256: str | None = None) -> None:
        folder = RECORDED / recording
        self.name = recording
        self.manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if prompt_sha256 is not None and self.manifest["prompt_sha256"] != prompt_sha256:
            raise ValueError(f"recording {recording!r} was made from a different prompt than the one asked for")
        self.prompt_sha256 = self.manifest["prompt_sha256"]
        self._replies: dict[tuple[str, int], str] = {}
        for line in (folder / "replies.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            self._replies[(row["item"], row["sample"])] = row["reply"]

    def reply(self, item: str, sample: int = 0) -> str:
        """The recorded reply for one item and sample. Raises KeyError when the recording has no such reply."""
        key = (item, sample)
        if key not in self._replies:
            raise KeyError(f"recording {self.name!r} has no reply for item {item!r}, sample {sample}")
        return self._replies[key]

    def keys(self) -> list[tuple[str, int]]:
        """Every (item, sample) pair in the recording, sorted."""
        return sorted(self._replies)
