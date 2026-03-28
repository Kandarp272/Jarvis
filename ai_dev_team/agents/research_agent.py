"""Research Agent – gathers documentation, APIs, and coding examples."""

from __future__ import annotations

import logging
from typing import Any

from ai_dev_team.config.settings import ProjectConfig
from ai_dev_team.core.agent_base import AgentBase
from ai_dev_team.core.communication_protocol import MessageBus
from ai_dev_team.core.task_manager import Task
from ai_dev_team.memory.memory_manager import MemoryManager
from ai_dev_team.tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class ResearchAgent(AgentBase):
    """Agent that researches technologies, best practices, and examples.

    Uses web search and long-term memory to build context for other agents.
    """

    def __init__(
        self,
        config: ProjectConfig,
        message_bus: MessageBus,
        memory: MemoryManager,
        search_tool: WebSearchTool | None = None,
    ) -> None:
        super().__init__(
            name="research_agent",
            role="researcher",
            config=config,
            message_bus=message_bus,
        )
        self.memory = memory
        self.search_tool = search_tool or WebSearchTool()

    async def analyze(self, task: Task) -> dict[str, Any]:
        """Determine what topics need researching."""
        keywords = self._extract_keywords(task.description)
        existing = self.memory.search_long_term(task.description, n_results=3)
        return {
            "keywords": keywords,
            "existing_knowledge": existing,
        }

    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Plan search queries."""
        keywords: list[str] = analysis.get("keywords", [])
        steps: list[dict[str, Any]] = []
        for kw in keywords:
            steps.append({"action": "search", "query": kw})
        steps.append({"action": "compile", "detail": "Merge results into a brief"})
        return steps

    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute search queries and compile findings."""
        findings: list[dict[str, Any]] = []

        for step in plan:
            if step["action"] == "search":
                results = await self.search_tool.search(step["query"])
                for r in results:
                    findings.append(
                        {"title": r.title, "url": r.url, "snippet": r.snippet}
                    )

        # Store in long-term memory for future use
        if findings:
            summary = self._compile_findings(findings)
            self.memory.store_long_term(
                doc_id=f"research-{task.task_id}",
                text=summary,
                metadata={"task": task.title, "type": "research"},
            )
        else:
            summary = (
                "No external search results available. Proceeding with "
                "built-in knowledge and best practices."
            )

        return {"summary": summary, "findings": findings}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """Naive keyword extraction – split on common delimiters."""
        stop = {
            "a", "an", "the", "is", "are", "for", "to", "of", "and",
            "in", "on", "with", "that", "this", "it", "as", "by", "be",
            "build", "create", "make", "write", "implement",
        }
        words = text.lower().split()
        unique: list[str] = []
        seen: set[str] = set()
        for w in words:
            cleaned = w.strip(".,;:!?\"'()[]{}").lower()
            if cleaned and cleaned not in stop and cleaned not in seen:
                seen.add(cleaned)
                unique.append(cleaned)
        # Return meaningful multi-word queries
        phrases = [text]  # full request first
        phrases.extend(unique[:5])
        return phrases

    @staticmethod
    def _compile_findings(findings: list[dict[str, Any]]) -> str:
        parts = ["## Research Findings\n"]
        for f in findings[:10]:
            parts.append(f"- **{f['title']}**: {f['snippet'][:200]}")
            if f.get("url"):
                parts.append(f"  Source: {f['url']}")
        return "\n".join(parts)
