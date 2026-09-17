"""Central configuration: paths, model names and retrieval tunables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Paths -----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

DOCS_DIR = PROJECT_ROOT / "docs"
INDEX_DIR = PROJECT_ROOT / "index"
INDEX_NAME = "docs_index"

# Chunking --------------------------------------------------------------------
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Retrieval -------------------------------------------------------------------
RETRIEVER_TOP_K = 4
MAX_CONTEXT_CHUNKS = 6

# Models ----------------------------------------------------------------------
# Verified live against the Generative Language API: gemini-2.5-flash and
# gemini-2.0-flash are retired, and text-embedding-004 is no longer served.
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.6-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

# Tried in order when building the LLM, so a retired model name degrades
# gracefully instead of failing the whole request.
CHAT_MODEL_CANDIDATES = (
    CHAT_MODEL,
    "gemini-flash-latest",
    "gemini-3.6-flash",
)

API_KEY_ENV_VAR = "GOOGLE_API_KEY"


def google_api_key() -> str:
    """Return the Google API key, raising a helpful error when it is absent."""
    key = os.getenv(API_KEY_ENV_VAR, "").strip()
    if not key:
        raise RuntimeError(
            f"{API_KEY_ENV_VAR} is not set. Add it to the .env file in "
            f"{PROJECT_ROOT} before building the index or asking questions."
        )
    return key


def index_files() -> tuple[Path, Path]:
    """Return the ``(faiss_store, docstore)`` paths for the persisted index."""
    return INDEX_DIR / f"{INDEX_NAME}.faiss", INDEX_DIR / f"{INDEX_NAME}.pkl"


def index_exists() -> bool:
    """True when a persisted FAISS index with its document store is present."""
    return all(path.exists() for path in index_files())
