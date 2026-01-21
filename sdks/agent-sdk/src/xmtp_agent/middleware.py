"""Middleware interfaces for the agent SDK."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

from xmtp_agent.context import ClientContext, ConversationContext, MessageContext

Handler = Callable[[MessageContext], Awaitable[None]]
ConversationHandler = Callable[[ConversationContext], Awaitable[None]]
LifecycleHandler = Callable[[ClientContext], Awaitable[None]]
NextHandler = Callable[[], Awaitable[None]]
ErrorNextHandler = Callable[[Exception | None], Awaitable[None]]
Middleware = Callable[[MessageContext, NextHandler], Awaitable[None]]
ErrorMiddleware = Callable[
    [Exception, MessageContext | ClientContext, ErrorNextHandler],
    Awaitable[None],
]


def backoff_reconnect(
    *,
    initial_delay: float = 0.5,
    max_delay: float = 30.0,
    multiplier: float = 2.0,
    reset_after: float = 60.0,
) -> ErrorMiddleware:
    """Return error middleware that handles stream errors with backoff."""

    delay = initial_delay
    last_error_at: float | None = None

    async def _middleware(
        error: Exception,
        context: MessageContext | ClientContext,
        next_handler: ErrorNextHandler,
    ) -> None:
        nonlocal delay, last_error_at
        from xmtp_agent.errors import AgentStreamingError

        if not isinstance(error, AgentStreamingError):
            await next_handler(error)
            return

        now = time.monotonic()
        if last_error_at is not None and (now - last_error_at) > reset_after:
            delay = initial_delay

        await asyncio.sleep(delay)
        last_error_at = now
        delay = min(max_delay, delay * multiplier)
        await next_handler(None)

    return _middleware


__all__ = [
    "ErrorMiddleware",
    "ErrorNextHandler",
    "Handler",
    "LifecycleHandler",
    "Middleware",
    "NextHandler",
    "ConversationHandler",
    "backoff_reconnect",
]
