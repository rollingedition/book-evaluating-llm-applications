"""The assistant under test, replayed: each chapter item's sections from BM25 over its own version, and the recorded
reply read back through ReplayModel and lib.contract. Chapter 1 reads twenty items, by id, and nothing else.
"""
from __future__ import annotations

from lib.contract import Reply, parse_reply
from lib.docs import Section, load_sections
from lib.prompts import answer_messages
from lib.replay import ReplayModel
from lib.retrieval import Retriever
from lib.testset import Item, load_items

CHAPTER_IDS = tuple(f"q-{number:04d}" for number in range(1, 21))  # the chapter's set (plan section 3.4)


def chapter_items() -> list[Item]:
    """The twenty chapter items, sorted by id. Raises if the test set does not hold them all."""
    wanted = set(CHAPTER_IDS)
    items = [item for item in load_items() if item.id in wanted]
    if len(items) != len(CHAPTER_IDS):
        raise ValueError(f"expected {len(CHAPTER_IDS)} chapter items, found {len(items)}")
    return items


class Assistant:
    """One recording of the assistant, its prompt, and BM25 over one version's sections per item.

    Retrieval is filtered: an item's sections come only from the index of the version it asks about.
    """

    def __init__(
        self, recording: str, system: str, prompt_sha256: str, k: int = 3, show_version: bool = False, live: bool = False
    ) -> None:
        # live=True is the reader's one-line swap: the pinned Qwen3-0.6B answers instead of the recording.
        # Imported only then, so replayed examples never load torch.
        if live:
            from lib.live import LiveModel

            self.model = LiveModel()
        else:
            self.model = ReplayModel(recording, prompt_sha256)
        self.live = live
        self.system = system
        self.k = k
        self.show_version = show_version
        self._indexes: dict[str, tuple[Retriever, dict[str, Section]]] = {}

    def _index(self, version: str) -> tuple[Retriever, dict[str, Section]]:
        """The retriever over one version's sections, and those sections by ID. Built once per version."""
        if version not in self._indexes:
            sections = load_sections(version)
            self._indexes[version] = (Retriever(sections), {s.section_id: s for s in sections})
        return self._indexes[version]

    def sections(self, item: Item) -> list[Section]:
        """The top k sections of the item's version for its question, in rank order."""
        retriever, by_id = self._index(item.version)
        return [by_id[hit.section_id] for hit in retriever.retrieve(item.question, self.k)]

    def context_ids(self, item: Item) -> frozenset[str]:
        """The section IDs that were in the item's prompt."""
        return frozenset(section.section_id for section in self.sections(item))

    def messages(self, item: Item) -> list[dict[str, str]]:
        """The chat messages the recording was made from for this item."""
        return answer_messages(self.system, item.question, self.sections(item), self.show_version)

    def reply(self, item: Item) -> Reply:
        """The reply for the item (sample 0), parsed with lib.contract: recorded, or live when live=True."""
        if self.live:
            return parse_reply(self.model.reply(self.messages(item), 0))
        return parse_reply(self.model.reply(item.id, 0))
