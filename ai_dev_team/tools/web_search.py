"""Web search tool for research agents."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single web search result."""

    title: str
    url: str
    snippet: str


class WebSearchTool:
    """Abstraction over web-search providers.

    The default implementation uses a simple HTTP-based approach.
    Swap in any search API (SerpAPI, Tavily, Brave Search, etc.) by
    subclassing and overriding ``_call_api``.
    """

    def __init__(self, api_key: str = "", provider: str = "tavily") -> None:
        self._api_key = api_key
        self._provider = provider

    async def search(
        self, query: str, num_results: int = 5
    ) -> list[SearchResult]:
        """Perform a web search and return results."""
        logger.info("Web search: %s (provider=%s)", query, self._provider)
        raw = await self._call_api(query, num_results)
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("snippet", r.get("content", "")),
            )
            for r in raw
        ]

    async def _call_api(
        self, query: str, num_results: int
    ) -> list[dict[str, Any]]:
        """Override this method to plug in a real search provider.

        The default returns an empty list so the system degrades gracefully
        when no API key is configured.
        """
        if not self._api_key:
            logger.warning("No search API key configured – returning empty results.")
            return []

        try:
            import httpx

            if self._provider == "tavily":
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": self._api_key,
                            "query": query,
                            "max_results": num_results,
                        },
                    )
                    resp.raise_for_status()
                    return resp.json().get("results", [])
        except Exception:
            logger.exception("Search API call failed")
            return []
        return []
