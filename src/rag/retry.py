"""Small retry helper for flaky network calls to the model APIs.

Google's endpoints occasionally drop a connection mid-request
(``httpx.RemoteProtocolError: Server disconnected without sending a
response``). The vendor SDK retries some of these internally, but not all,
and an exhausted retry currently surfaces as a raw traceback. This module
gives every network-touching call in the pipeline a bounded, backed-off retry
so a transient blip degrades into a clear message instead of a crash.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_ATTEMPTS = 3
BASE_DELAY_SECONDS = 1.5
BACKOFF_FACTOR = 2.0


def call_with_retries(
    operation: Callable[[], T],
    *,
    description: str,
    attempts: int = DEFAULT_ATTEMPTS,
    base_delay: float = BASE_DELAY_SECONDS,
) -> T:
    """Run ``operation`` up to ``attempts`` times with exponential backoff.

    Re-raises the last exception when every attempt fails, so callers can
    still decide how to report the failure.
    """
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as error:  # noqa: BLE001 - any transport error is retryable
            last_error = error
            if attempt == attempts:
                break
            delay = base_delay * (BACKOFF_FACTOR ** (attempt - 1))
            logger.warning(
                "%s failed (attempt %d/%d): %s. Retrying in %.1fs.",
                description,
                attempt,
                attempts,
                error,
                delay,
            )
            time.sleep(delay)

    assert last_error is not None
    raise last_error
