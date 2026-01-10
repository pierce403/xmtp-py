"""Middleware interfaces for the agent SDK."""

from __future__ import annotations

from typing import Awaitable, Callable, Protocol

from xmtp_agent.context import ClientContext, ConversationContext, MessageContext

Handler = Callable[[MessageContext], Awaitable[None]]
ConversationHandler = Callable[[ConversationContext], Awaitable[None]]
LifecycleHandler = Callable[[ClientContext], Awaitable[None]]


class Middleware(Protocol):
    """Middleware interface for message handling."""

    async def __call__(self, ctx: MessageContext, next_handler: Handler) -> None:
        """Invoke the middleware with a next handler."""


class ErrorMiddleware(Protocol):
    """Middleware interface for error handling."""

    async def __call__(self, error: Exception) -> None:
        """Handle an error."""
