"""Stages 4 and 5: grounded prompt construction, LLM call, cited answer."""

from __future__ import annotations

import logging

from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage

from .config import RETRIEVER_TOP_K
from .llm import get_llm, text_of
from .retry import call_with_retries
from .schema import Answer, Citation, RetrievedChunk
from .vectorstore import retrieve

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a retrieval-augmented assistant that answers strictly from the "
    "provided document excerpts.\n\n"
    "Rules:\n"
    "1. Use only the numbered excerpts in the CONTEXT section. Never rely on "
    "outside knowledge.\n"
    "2. Cite every claim with the bracketed number of the excerpt it came "
    "from, for example [1] or [2][3].\n"
    "3. If the excerpts do not contain the answer, reply exactly: "
    "\"I could not find that in the provided documents.\" and add nothing else.\n"
    "4. Answer in the same language as the question, in at most 3 short "
    "paragraphs. Be specific and quote short phrases where useful."
)

NO_ANSWER_TEXT = "I could not find that in the provided documents."


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as numbered, citable excerpts."""
    if not chunks:
        return "(no excerpts retrieved)"
    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        body = " ".join(chunk.text.split())
        blocks.append(f"[{index}] source: {chunk.source_name} (page {chunk.page_number})\n{body}")
    return "\n\n".join(blocks)


def build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    """Combine the context and the question into one grounded user message."""
    return (
        f"CONTEXT\n{build_context(chunks)}\n\n"
        f"QUESTION\n{question}\n\n"
        "Answer using only the excerpts above and cite them with [n] markers."
    )


def to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    """Number the retrieved chunks so the UI can match ``[n]`` markers."""
    return [
        Citation(
            index=index,
            source_name=chunk.source_name,
            page_number=chunk.page_number,
            score=chunk.score,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]


def answer_question(
    store: FAISS,
    question: str,
    k: int = RETRIEVER_TOP_K,
) -> Answer:
    """Retrieve, generate a grounded answer, and attach its citations."""
    cleaned_question = question.strip()
    if not cleaned_question:
        return Answer(question=question, text="Please enter a question.", grounded=False)

    try:
        chunks = retrieve(store, cleaned_question, k=k)
    except Exception as error:
        logger.exception("Retrieval failed")
        return Answer(
            question=cleaned_question,
            text=(
                "Retrieval failed before the model was called "
                f"({type(error).__name__}: {error}). Check your network connection "
                "and try again."
            ),
            grounded=False,
        )

    citations = to_citations(chunks)

    if not chunks:
        return Answer(
            question=cleaned_question,
            text=NO_ANSWER_TEXT,
            citations=[],
            chunks=[],
            grounded=False,
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_prompt(cleaned_question, chunks)),
    ]

    try:
        llm = get_llm()
        reply = call_with_retries(
            lambda: llm.invoke(messages),
            description="Generating an answer",
        )
        answer_text = text_of(reply)
    except Exception as error:
        logger.exception("Generation failed")
        return Answer(
            question=cleaned_question,
            text=(
                "Generation failed after retrying "
                f"({type(error).__name__}: {error}). The retrieved sources are "
                "shown below."
            ),
            citations=citations,
            chunks=chunks,
            grounded=False,
        )

    grounded = NO_ANSWER_TEXT.rstrip(".") not in answer_text
    return Answer(
        question=cleaned_question,
        text=answer_text or NO_ANSWER_TEXT,
        citations=citations,
        chunks=chunks,
        grounded=grounded,
    )
