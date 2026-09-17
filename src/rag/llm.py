"""Chat model construction.

Google retires model names without notice (``gemini-2.5-flash`` and
``gemini-2.0-flash`` both now return 404 for new users), so the model is
probed once and the first working candidate is cached for the process.
"""

from __future__ import annotations

import logging

from langchain_google_genai import ChatGoogleGenerativeAI

from .config import CHAT_MODEL_CANDIDATES, google_api_key

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 1024

_cached_llm: ChatGoogleGenerativeAI | None = None
_cached_model_name: str | None = None


def build_llm(model: str) -> ChatGoogleGenerativeAI:
    """Construct a chat model for an explicit model name.

    ``temperature`` is deliberately not set: current Gemini flash models use
    fixed sampling defaults and warn that the parameter is ignored.
    """
    return ChatGoogleGenerativeAI(
        model=model,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        google_api_key=google_api_key(),
    )


def text_of(message: object) -> str:
    """Flatten a LangChain message's ``content`` into plain text.

    langchain-google-genai 4.x returns content as a list of typed blocks
    (``[{"type": "text", "text": ..., "extras": {...}}]``) rather than a
    string, and the extras carry large thought signatures that must not leak
    into the UI.
    """
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join(part for part in parts if part).strip()
    return str(content).strip()


def _verify(model: str) -> ChatGoogleGenerativeAI:
    """Build the model and make one tiny call to confirm it is served."""
    llm = build_llm(model)
    llm.invoke("ping")
    return llm


def get_llm() -> ChatGoogleGenerativeAI:
    """Return a cached chat model, trying each candidate until one answers."""
    global _cached_llm, _cached_model_name

    if _cached_llm is not None:
        return _cached_llm

    failures: list[str] = []
    for candidate in dict.fromkeys(CHAT_MODEL_CANDIDATES):
        try:
            _cached_llm = _verify(candidate)
        except Exception as error:
            failures.append(f"{candidate} ({type(error).__name__})")
            logger.warning("Chat model %s unavailable: %s", candidate, error)
            continue
        _cached_model_name = candidate
        logger.info("Using chat model %s", candidate)
        return _cached_llm

    raise RuntimeError(
        "No usable Google chat model. Tried: " + ", ".join(failures)
    )


def active_model_name() -> str:
    """Name of the model in use, or the first configured candidate."""
    return _cached_model_name or CHAT_MODEL_CANDIDATES[0]
