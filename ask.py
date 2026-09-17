"""Ask a question against the indexed corpus from the command line.

Usage:
    python ask.py "how many days of annual leave do employees get?"
    python ask.py --top-k 6 --show-chunks "what is the API rate limit?"
    python ask.py            # interactive prompt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.chain import answer_question  # noqa: E402
from src.rag.config import RETRIEVER_TOP_K, index_exists  # noqa: E402
from src.rag.embeddings import get_embeddings  # noqa: E402
from src.rag.llm import active_model_name, get_llm  # noqa: E402
from src.rag.vectorstore import get_or_build_index  # noqa: E402


def print_answer(question: str, store, top_k: int, show_chunks: bool) -> None:
    """Retrieve, answer, and print the result with its sources."""
    result = answer_question(store, question, k=top_k)

    print()
    print(f"Q: {question}")
    print(f"A: {result.text}")
    print()

    if result.citations:
        print("Sources:")
        for citation in result.citations:
            print(f"  {citation.label}  (similarity {citation.score:.3f})")
    else:
        print("Sources: none")

    if show_chunks:
        print()
        print("Retrieved chunks:")
        for index, chunk in enumerate(result.chunks, start=1):
            print(f"  [{index}] {chunk.label}  score={chunk.score:.3f}")
            print(f"      {chunk.preview(220)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="*", help="the question to ask")
    parser.add_argument("--top-k", type=int, default=RETRIEVER_TOP_K, help="chunks to retrieve")
    parser.add_argument("--show-chunks", action="store_true", help="print retrieved chunk text")
    args = parser.parse_args()

    try:
        embeddings = get_embeddings()
        if not index_exists():
            print("No index found; building one from docs/ (this calls the embedding API).")
        store = get_or_build_index(embeddings)
        print(f"Chat model: {active_model_name()}")
        get_llm()
    except Exception as error:
        print(f"Startup failed: {type(error).__name__}: {error}", file=sys.stderr)
        print("Check GOOGLE_API_KEY in .env and your network connection.", file=sys.stderr)
        return 1

    question = " ".join(args.question).strip()
    if question:
        print_answer(question, store, args.top_k, args.show_chunks)
        return 0

    print("Interactive mode. Type a question, or 'exit' to quit.")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if question.lower() in {"exit", "quit", ":q"}:
            return 0
        if question:
            print_answer(question, store, args.top_k, args.show_chunks)


if __name__ == "__main__":
    raise SystemExit(main())
