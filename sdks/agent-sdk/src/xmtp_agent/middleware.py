"""Middleware interfaces for the agent SDK."""

from __future__ import annotations

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
