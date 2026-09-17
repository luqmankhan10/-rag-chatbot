"""Shared data structures passed between pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievedChunk:
    """A single chunk returned by the retriever."""

    text: str
    source_name: str
    page_number: int
    score: float

    @property
    def label(self) -> str:
        """Human readable citation label, e.g. ``handbook.pdf p.4``."""
        return f"{self.source_name} p.{self.page_number}"

    def preview(self, limit: int = 400) -> str:
        """Trimmed chunk body for display in the UI."""
        body = " ".join(self.text.split())
        if len(body) <= limit:
            return body
        return f"{body[:limit].rstrip()}..."


@dataclass(frozen=True)
class Citation:
    """A source the answer is grounded in."""

    index: int
    source_name: str
    page_number: int
    score: float
    path: str = ""

    @property
    def label(self) -> str:
        return f"[{self.index}] {self.source_name} p.{self.page_number}"


@dataclass
class Answer:
    """Final answer plus the evidence it was built from."""

    question: str
    text: str
    citations: list[Citation] = field(default_factory=list)
    chunks: list[RetrievedChunk] = field(default_factory=list)
    grounded: bool = True

    @property
    def has_citations(self) -> bool:
        return bool(self.citations)

    def sources_markdown(self) -> str:
        """Markdown bullet list of the cited sources."""
        if not self.citations:
            return "_No source chunks were retrieved._"
        return "\n".join(
            f"- **{citation.label}** &mdash; {citation.path or citation.source_name}"
            for citation in self.citations
        )
