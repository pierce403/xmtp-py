"""Command router middleware for XMTP agents."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from xmtp_agent.context import MessageContext
from xmtp_agent.middleware import Middleware

Handler = Callable[[MessageContext], Awaitable[None]]


class CommandRouter:
    """Route slash commands to handlers for text messages."""

    def __init__(self) -> None:
        self._commands: dict[str, Handler] = {}
        self._default: Handler | None = None

    @property
    def command_list(self) -> list[str]:
        return list(self._commands.keys())

    def command(self, command: str, handler: Handler) -> CommandRouter:
        if not command.startswith("/"):
            raise ValueError('Command must start with "/"')
        self._commands[command.lower()] = handler
        return self

    def default(self, handler: Handler) -> CommandRouter:
        self._default = handler
        return self

    async def handle(self, ctx: MessageContext) -> bool:
        if not ctx.is_text():
            return False
        message_text = ctx.message.content
        if not isinstance(message_text, str):
            return False
        parts = message_text.split(" ")
        command = parts[0].lower() if parts else ""
        if not command:
            return False
        if command.startswith("/"):
            handler = self._commands.get(command)
            if handler:
                ctx.message.content = " ".join(parts[1:])
                await handler(ctx)
                return True
        if self._default:
            await self._default(ctx)
            return True
        return False

    def middleware(self) -> Middleware:
        async def _middleware(
            ctx: MessageContext,
            next_handler: Callable[[], Awaitable[None]],
        ) -> None:
            handled = await self.handle(ctx)
            if not handled:
                await next_handler()

        return _middleware


__all__ = ["CommandRouter"]
