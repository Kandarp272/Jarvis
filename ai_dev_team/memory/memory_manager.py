"""Unified memory manager combining short-term and long-term memory."""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from ai_dev_team.config.settings import MemoryConfig
from ai_dev_team.memory.vector_memory import VectorMemory

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single entry in short-term memory."""

    key: str
    value: Any
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """Combines a fixed-size short-term buffer with a persistent vector store.

    * **Short-term**: recent tasks, conversation context (FIFO buffer).
    * **Long-term**: previous projects, learned solutions, architecture
      patterns (persisted in ChromaDB).
    """

    SHORT_TERM_CAPACITY = 100

    def __init__(self, config: MemoryConfig) -> None:
        self._short_term: deque[MemoryEntry] = deque(
            maxlen=self.SHORT_TERM_CAPACITY
        )
        self._long_term = VectorMemory(config)

    # ------------------------------------------------------------------
    # Short-term memory
    # ------------------------------------------------------------------

    def remember(
        self,
        key: str,
        value: Any,
        category: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store an item in short-term memory."""
        self._short_term.append(
            MemoryEntry(key=key, value=value, category=category, metadata=metadata or {})
        )

    def recall_short_term(
        self, category: str | None = None
    ) -> list[MemoryEntry]:
        """Retrieve recent short-term entries, optionally filtered."""
        if category is None:
            return list(self._short_term)
        return [e for e in self._short_term if e.category == category]

    # ------------------------------------------------------------------
    # Long-term memory
    # ------------------------------------------------------------------

    def store_long_term(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._long_term.store(doc_id, text, metadata)

    def search_long_term(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self._long_term.search(query, n_results=n_results, where=where)

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def build_context(self, query: str, max_items: int = 10) -> str:
        """Produce a combined context string for LLM prompts."""
        parts: list[str] = []

        # Recent short-term
        recent = list(self._short_term)[-max_items:]
        if recent:
            parts.append("## Recent Context")
            for entry in recent:
                parts.append(f"- [{entry.category}] {entry.key}: {_truncate(entry.value)}")

        # Relevant long-term
        lt_results = self._long_term.search(query, n_results=max_items)
        if lt_results:
            parts.append("\n## Relevant Past Knowledge")
            for doc in lt_results:
                parts.append(f"- {doc['text'][:300]}")

        return "\n".join(parts)


def _truncate(value: Any, length: int = 200) -> str:
    text = json.dumps(value) if not isinstance(value, str) else value
    return text[:length] + ("..." if len(text) > length else "")
