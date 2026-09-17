"""Stage 1 of the pipeline: load PDFs and split them into overlapping chunks."""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CHUNK_OVERLAP, CHUNK_SIZE, DOCS_DIR

logger = logging.getLogger(__name__)


def pdf_files(docs_dir: Path | None = None) -> list[Path]:
    """Return every PDF in ``docs_dir`` sorted by file name."""
    directory = docs_dir or DOCS_DIR
    if not directory.exists():
        return []
    return sorted(
        path for path in directory.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"
    )


def _load_with_pypdf(path: Path) -> list[Document]:
    """Load a PDF with LangChain's ``PyPDFLoader``."""
    return PyPDFLoader(str(path)).load()


def _load_with_repair(path: Path) -> list[Document]:
    """Fall back to a lenient pypdf read for PDFs with a damaged xref table."""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(path), strict=False)
    repaired = PdfWriter()
    for page in reader.pages:
        repaired.add_page(page)

    target = path.with_name(f"{path.stem}__repaired.pdf")
    with target.open("wb") as handle:
        repaired.write(handle)
    logger.warning("Repaired damaged PDF %s -> %s", path.name, target.name)
    return _load_with_pypdf(target)


def load_pdf_documents(path: Path) -> list[Document]:
    """Load one PDF, repairing it if the xref table is malformed."""
    try:
        return _load_with_pypdf(path)
    except Exception as error:
        logger.warning("PyPDFLoader failed on %s (%s); attempting repair.", path.name, error)
        return _load_with_repair(path)


def normalize_metadata(documents: list[Document]) -> list[Document]:
    """Add ``source_name``/``page_number`` keys used by the citation layer."""
    for document in documents:
        source = Path(str(document.metadata.get("source", "unknown.pdf")))
        page_index = int(document.metadata.get("page", 0) or 0)
        document.metadata["source_name"] = source.name
        document.metadata["page_number"] = page_index + 1
        document.metadata["source"] = str(source)
    return documents


def load_documents(docs_dir: Path | None = None) -> list[Document]:
    """Load every PDF in the corpus and normalise its metadata."""
    pages: list[Document] = []
    for path in pdf_files(docs_dir):
        loaded = load_pdf_documents(path)
        pages.extend(loaded)
        logger.info("Loaded %s (%d pages)", path.name, len(loaded))
    return normalize_metadata(pages)


def split_documents(documents: list[Document]) -> list[Document]:
    """Split pages into overlapping chunks, preserving source metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def load_and_split(docs_dir: Path | None = None) -> list[Document]:
    """Convenience helper: load the corpus and return its chunks."""
    return split_documents(load_documents(docs_dir))
