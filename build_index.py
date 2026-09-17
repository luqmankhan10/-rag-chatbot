"""Build or rebuild the FAISS vector index from every PDF in ``docs/``.

Usage:
    python build_index.py            # build, reusing nothing
    python build_index.py --purge    # delete the existing index first
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.config import EMBEDDING_MODEL, index_files  # noqa: E402
from src.rag.embeddings import get_embeddings  # noqa: E402
from src.rag.ingest import load_and_split, pdf_files  # noqa: E402
from src.rag.retry import call_with_retries  # noqa: E402
from src.rag.vectorstore import build_index, save_index  # noqa: E402

logger = logging.getLogger("build_index")


def purge_index() -> int:
    """Delete the persisted index files; return how many were removed."""
    removed = 0
    for path in index_files():
        if path.exists():
            path.unlink()
            removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--purge", action="store_true", help="delete the existing index first")
    parser.add_argument("--show-chunks", type=int, default=2, help="how many chunk previews to print")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    documents = pdf_files()
    if not documents:
        logger.error("No PDFs found in docs/. Add your own, or run:")
        logger.error("  python tools/make_sample_docs.py")
        return 1

    if args.purge:
        removed = purge_index()
        logger.info("Purged %d existing index file(s).", removed)

    logger.info("Corpus: %d PDF(s) in docs/", len(documents))
    for path in documents:
        logger.info("  - %s", path.name)

    started = time.perf_counter()

    chunks = load_and_split()
    if not chunks:
        logger.error("PDFs produced no text chunks. Nothing to index.")
        return 1
    logger.info("Split into %d chunks (size 800, overlap 100).", len(chunks))

    embeddings = get_embeddings()
    logger.info("Embedding with %s ...", EMBEDDING_MODEL)

    try:
        store = call_with_retries(
            lambda: build_index(chunks, embeddings),
            description="Embedding chunks and building the index",
        )
    except Exception as error:
        logger.error("Failed to build the index: %s: %s", type(error).__name__, error)
        return 1

    folder = save_index(store)
    elapsed = time.perf_counter() - started

    store_file, doc_file = index_files()
    logger.info("Vectors in index: %d", store.index.ntotal)
    logger.info("Saved %s (%.1f KB)", store_file.name, store_file.stat().st_size / 1024)
    logger.info("Saved %s (%.1f KB)", doc_file.name, doc_file.stat().st_size / 1024)
    logger.info("Index folder: %s", folder)
    logger.info("Done in %.1fs.", elapsed)

    for index, chunk in enumerate(chunks[: max(args.show_chunks, 0)], start=1):
        source = chunk.metadata.get("source_name", "?")
        page = chunk.metadata.get("page_number", "?")
        preview = " ".join(chunk.page_content.split())[:160]
        logger.info("chunk %d [%s p.%s]: %s...", index, source, page, preview)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
