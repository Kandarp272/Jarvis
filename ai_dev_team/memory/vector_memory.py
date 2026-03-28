"""Vector-based long-term memory backed by ChromaDB."""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from ai_dev_team.config.settings import MemoryConfig

logger = logging.getLogger(__name__)


class VectorMemory:
    """Persistent vector store for agent knowledge.

    Wraps a ChromaDB collection and provides simple
    ``store`` / ``search`` / ``delete`` operations.
    """

    def __init__(self, config: MemoryConfig) -> None:
        self._config = config
        self._client = chromadb.Client(
            ChromaSettings(
                anonymized_telemetry=False,
                is_persistent=True,
                persist_directory=config.persist_directory,
            )
        )
        self._collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "VectorMemory initialised – collection=%s, docs=%d",
            config.collection_name,
            self._collection.count(),
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def store(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Upsert a document into the collection."""
        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the closest documents to *query*."""
        kwargs: dict[str, Any] = {
            "query_texts": [query],
            "n_results": min(n_results, max(self._collection.count(), 1)),
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        docs: list[dict[str, Any]] = []
        if results and results["ids"]:
            for idx, doc_id in enumerate(results["ids"][0]):
                docs.append(
                    {
                        "id": doc_id,
                        "text": (results["documents"] or [[]])[0][idx]
                        if results["documents"]
                        else "",
                        "metadata": (results["metadatas"] or [[]])[0][idx]
                        if results["metadatas"]
                        else {},
                        "distance": (results["distances"] or [[]])[0][idx]
                        if results["distances"]
                        else None,
                    }
                )
        return docs

    def delete(self, doc_id: str) -> None:
        """Remove a document by id."""
        self._collection.delete(ids=[doc_id])

    @property
    def count(self) -> int:
        return self._collection.count()
