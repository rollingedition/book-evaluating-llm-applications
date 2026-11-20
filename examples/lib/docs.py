"""The sablefile docs in their three versions, split into sections.

A section is one `##` or `###` heading with its explicit `{#section-id}`, and the text up to the next such heading.
CHANGELOG.md files are not doc pages and are skipped. A heading without an ID, or an ID that is malformed or repeated
within one version, is an error.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "data" / "docs"
SECTION_ID = re.compile(r"^[a-z][a-z0-9-]*$")
HEADING = re.compile(r"^(##|###) +(.+?)\s*\{#([^}]*)\}\s*$")


@dataclass(frozen=True)
class Section:
    """One section of one version: its ID, its heading text without the ID, and its body."""

    version: str
    section_id: str
    title: str
    text: str


def versions() -> list[str]:
    """The doc versions present, sorted."""
    return sorted(p.name for p in DOCS.iterdir() if p.is_dir())


def load_sections(version: str | None = None) -> list[Section]:
    """All sections of one version, or of every version when `version` is None, sorted by (version, section_id)."""
    found: list[Section] = []
    for v in [version] if version else versions():
        seen: set[str] = set()
        for path in sorted((DOCS / v).glob("*.md")):
            if path.name == "CHANGELOG.md":
                continue
            for section in _split(path.read_text(encoding="utf-8"), v, path.name):
                if section.section_id in seen:
                    raise ValueError(f"version {v}: section ID {section.section_id!r} appears twice")
                seen.add(section.section_id)
                found.append(section)
    return sorted(found, key=lambda s: (s.version, s.section_id))


def _split(text: str, version: str, name: str) -> list[Section]:
    """The sections of one file. Lines before the first heading are not part of any section."""
    sections: list[Section] = []
    heading: re.Match[str] | None = None
    body: list[str] = []

    def close() -> None:
        if heading is not None:
            sid = heading.group(3).strip()
            if not SECTION_ID.match(sid):
                raise ValueError(f"{version}/{name}: section ID {sid!r} is not lowercase words and hyphens")
            sections.append(Section(version, sid, heading.group(2).strip(), "\n".join(body).strip()))

    for line in text.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            close()
            heading = HEADING.match(line)
            if heading is None:
                raise ValueError(f"{version}/{name}: a heading has no {{#section-id}}: {line[:60]!r}")
            body = []
        elif heading is not None:
            body.append(line)
    close()
    return sections
