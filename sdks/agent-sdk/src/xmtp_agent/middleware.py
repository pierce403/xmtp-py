"""Middleware interfaces for the agent SDK."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from xmtp_agent.context import ClientContext, ConversationContext, MessageContext

Handler = Callable[[Any], Awaitable[None]]
ConversationHandler = Callable[[Any], Awaitable[None]]
LifecycleHandler = Callable[[Any], Awaitable[None]]
NextHandler = Callable[[], Awaitable[None]]
ErrorNextHandler = Callable[[Exception | None], Awaitable[None]]
Middleware = Callable[[Any, NextHandler], Awaitable[None]]
ErrorMiddleware = Callable[[Exception, Any, ErrorNextHandler], Awaitable[None]]
