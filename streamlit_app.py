"""Streamlit chat UI for the docs RAG pipeline.

Run from the project root:
    python -m streamlit run streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.chain import NO_ANSWER_TEXT, answer_question  # noqa: E402
from src.rag.config import (  # noqa: E402
    MAX_CONTEXT_CHUNKS,
    RETRIEVER_TOP_K,
    index_exists,
)
from src.rag.embeddings import get_embeddings  # noqa: E402
from src.rag.llm import active_model_name  # noqa: E402
from src.rag.vectorstore import get_or_build_index  # noqa: E402


st.set_page_config(page_title="Docs RAG Chat", page_icon="📄", layout="wide")


@st.cache_resource(show_spinner="Loading the document index...")
def load_store():
    """Load (or build) the FAISS index once per process."""
    return get_or_build_index(get_embeddings())


def ensure_state() -> None:
    """Create the chat history on first run."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_sources(answer) -> None:
    """Show the retrieved chunks for an answer, collapsed by default."""
    if not answer.chunks:
        return
    shown = answer.chunks[:MAX_CONTEXT_CHUNKS]
    with st.expander(f"Sources ({len(shown)})", expanded=False):
        for chunk in shown:
            st.markdown(
                f"**{chunk.label}** &nbsp;·&nbsp; similarity `{chunk.score}`"
            )
            st.caption(chunk.preview())
            st.divider()


def main() -> None:
    ensure_state()

    st.title("📄 Document Q&A")
    st.caption("Answers are grounded strictly in the indexed PDFs and cite their sources.")

    with st.sidebar:
        st.header("Settings")
        top_k = st.slider("Chunks to retrieve", 1, 8, RETRIEVER_TOP_K)
        st.metric("Chat model", active_model_name())
        st.metric("Index on disk", "yes" if index_exists() else "no (will build)")
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        st.divider()
        st.caption("Try: *How many days of paid annual leave do full time employees receive?*")

    # Replay the conversation on every rerun.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("answer"):
                render_sources(message["answer"])

    question = st.chat_input("Ask a question about your documents...")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving and answering..."):
                store = load_store()
                answer = answer_question(store, question, k=top_k)
        except Exception as error:  # surface config/network faults in the UI
            text = (
                f"**Something went wrong** (`{type(error).__name__}`)\n\n"
                f"{error}\n\n"
                "Check that `.env` has a valid `GOOGLE_API_KEY` and that you are online."
            )
            st.error(text)
            st.session_state.messages.append(
                {"role": "assistant", "content": text, "answer": None}
            )
            return

        st.markdown(answer.text)
        if answer.grounded and answer.citations:
            st.caption("Sources: " + " · ".join(c.label for c in answer.citations))
        elif answer.text.strip() == NO_ANSWER_TEXT:
            st.info("The indexed documents do not cover this question.")

        render_sources(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer.text, "answer": answer}
    )


main()
