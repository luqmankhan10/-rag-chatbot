"""Retrieval-Augmented Generation chatbot package.

Pipeline stages live in dedicated modules:

``ingest``      PDF loading + overlapping chunking
``vectorstore`` FAISS persistence and retrieval
``chain``       grounded prompt construction + LLM answer with citations
``config``      paths, model names and tunables
``schema``      shared dataclasses
"""

from .config import (
    CHAT_MODEL,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCS_DIR,
    EMBEDDING_MODEL,
    INDEX_DIR,
    RETRIEVER_TOP_K,
)
from .schema import Answer, Citation, RetrievedChunk

__all__ = [
    "Answer",
    "CHAT_MODEL",
    "CHUNK_OVERLAP",
    "CHUNK_SIZE",
    "Citation",
    "DOCS_DIR",
    "EMBEDDING_MODEL",
    "INDEX_DIR",
    "RETRIEVER_TOP_K",
    "RetrievedChunk",
]
