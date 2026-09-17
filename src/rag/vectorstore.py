"""Stage 2 and 3 of the pipeline: persist embeddings in FAISS and retrieve."""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from .config import INDEX_DIR, INDEX_NAME, RETRIEVER_TOP_K, index_files
from .retry import call_with_retries
from .schema import RetrievedChunk

logger = logging.getLogger(__name__)


def build_index(chunks: list[Document], embeddings: Embeddings) -> FAISS:
    """Embed every chunk and build an in-memory FAISS index."""
    if not chunks:
        raise ValueError("Cannot build an index from zero chunks. Add PDFs to docs/.")
    return FAISS.from_documents(chunks, embeddings)


def save_index(store: FAISS, folder: Path | None = None) -> Path:
    """Persist the index and its document store to disk."""
    target = folder or INDEX_DIR
    target.mkdir(parents=True, exist_ok=True)
    store.save_local(str(target), index_name=INDEX_NAME)
    logger.info("Saved FAISS index to %s", target)
    return target


def load_index(embeddings: Embeddings, folder: Path | None = None) -> FAISS:
    """Load a persisted FAISS index.

    ``allow_dangerous_deserialization`` is required because the document store
    is a pickle. It is safe here: the file is generated locally by
    ``build_index.py`` from this repository's own PDFs, never downloaded.
    """
    source = folder or INDEX_DIR
    store_file, doc_file = index_files()
    if not (store_file.exists() and doc_file.exists()):
        raise FileNotFoundError(
            f"No index found at {source}. Run 'python build_index.py' first."
        )
    return FAISS.load_local(
        str(source),
        embeddings,
        index_name=INDEX_NAME,
        allow_dangerous_deserialization=True,
    )


def get_or_build_index(embeddings: Embeddings) -> FAISS:
    """Load the persisted index when present, otherwise build it from disk."""
    from .config import index_exists
    from .ingest import load_and_split

    if index_exists():
        return load_index(embeddings)

    logger.info("No index on disk; building one from docs/.")
    store = build_index(load_and_split(), embeddings)
    save_index(store)
    return store


def _metadata_str(document: Document, key: str, fallback: str) -> str:
    """Read a string metadata value with a safe fallback."""
    value = document.metadata.get(key, fallback)
    return value if isinstance(value, str) and value else fallback


def _metadata_int(document: Document, key: str, fallback: int = 0) -> int:
    """Read an integer metadata value, tolerating strings and ``None``."""
    value = document.metadata.get(key, fallback)
    if isinstance(value, bool) or value is None:
        return fallback
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return fallback


def to_retrieved_chunk(document: Document, distance: float) -> RetrievedChunk:
    """Convert a scored FAISS hit into a citation-ready chunk.

    FAISS returns L2 distance, so a smaller number means a closer match; it is
    mapped to a 0-1 similarity where 1 is an exact match.
    """
    similarity = 1.0 / (1.0 + max(distance, 0.0))
    return RetrievedChunk(
        text=document.page_content,
        source_name=_metadata_str(document, "source_name", "unknown.pdf"),
        page_number=_metadata_int(document, "page_number"),
        score=round(similarity, 4),
    )


def retrieve(store: FAISS, question: str, k: int = RETRIEVER_TOP_K) -> list[RetrievedChunk]:
    """Return the top-k chunks for a question, best match first.

    The query is embedded before FAISS runs, so this call hits the network and
    is retried on transient transport failures.
    """
    hits = call_with_retries(
        lambda: store.similarity_search_with_score(question, k=k),
        description=f"Retrieving top-{k} chunks",
    )
    return [to_retrieved_chunk(document, distance) for document, distance in hits]


def as_retriever(store: FAISS, k: int = RETRIEVER_TOP_K):
    """LangChain retriever view of the index, used when composing chains."""
    return store.as_retriever(search_kwargs={"k": k})
