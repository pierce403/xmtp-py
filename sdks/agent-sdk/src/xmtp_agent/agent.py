"""Agent class for XMTP."""

from __future__ import annotations

import asyncio
import inspect
import os
import warnings
from collections import defaultdict
from collections.abc import Awaitable, Callable

from xmtp import Client, ClientOptions, Conversation, DecodedMessage, Dm, Group
from xmtp.async_stream import AsyncStream
from xmtp.bindings import NativeBindings
from xmtp.env import load_client_options_from_env, load_signer_from_env
from xmtp.signers.base import Signer
from xmtp.types import LogLevel

from xmtp_agent.context import ClientContext, ConversationContext, MessageContext
from xmtp_agent.debug import get_installation_info
from xmtp_agent.errors import AgentError, AgentStreamingError
from xmtp_agent.filters import (
    from_self,
    has_content,
    is_group_update,
    is_markdown,
    is_reaction,
    is_read_receipt,
    is_remote_attachment,
    is_reply,
    is_text,
    is_transaction_reference,
    is_wallet_send_calls,
)
from xmtp_agent.middleware import ErrorMiddleware, Middleware

EventPayload = ClientContext | ConversationContext | MessageContext | Exception
EventHandler = Callable[[EventPayload], Awaitable[None] | None]


class _ErrorRegistrar:
    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    def use(self, *error_middlewares: ErrorMiddleware | list[ErrorMiddleware]) -> _ErrorRegistrar:
        for middleware in error_middlewares:
            if isinstance(middleware, list):
                self._agent._error_middlewares.extend(middleware)
            else:
                self._agent._error_middlewares.append(middleware)
        return self


class Agent:
    """Main agent class with an event-driven API."""

    def __init__(self, client: Client) -> None:
        self._client = client
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._middlewares: list[Middleware] = []
        self._error_middlewares: list[ErrorMiddleware] = []
        self._errors = _ErrorRegistrar(self)
        self._conversation_stream_handle: (
            AsyncStream[Conversation | NativeBindings.FfiSubscribeError] | None
        ) = None
        self._message_stream_handle: (
            AsyncStream[DecodedMessage[object] | NativeBindings.FfiSubscribeError] | None
        ) = None
        self._conversation_stream: asyncio.Task[None] | None = None
        self._message_stream: asyncio.Task[None] | None = None
        self._running = False

    @classmethod
    async def create(
        cls,
        signer: Signer,
        options: ClientOptions | None = None,
    ) -> Agent:
        """Create an agent with a signer."""

        opts = options or ClientOptions()
        if opts.app_version is None:
            opts.app_version = "agent-sdk/alpha"
        if not opts.disable_device_sync:
            opts.disable_device_sync = True

        if os.getenv("XMTP_FORCE_DEBUG"):
            opts.debug_events_enabled = True
            opts.structured_logging = True
            level = os.getenv("XMTP_FORCE_DEBUG_LEVEL")
            try:
                opts.logging_level = LogLevel(level) if level else LogLevel.WARN
            except ValueError:
                opts.logging_level = LogLevel.WARN

        client = await Client.create(signer, opts)
        info = await get_installation_info(client)
        if info.total_installations > 1 and info.is_most_recent:
            warnings.warn(
                "You have multiple installations. Installation ID "
                f'"{info.installation_id}" is the most recent. Persist and reload your '
                "installation data to avoid losing access. If you exceed the installation "
                "limit, your agent will stop working. See "
                "https://docs.xmtp.org/agents/build-agents/local-database"
                "#installation-limits-and-revocation-rules",
                UserWarning,
                stacklevel=2,
            )
        return cls(client)

    @classmethod
    async def create_from_env(cls, options: ClientOptions | None = None) -> Agent:
        """Create an agent from environment variables."""

        signer = load_signer_from_env()
        opts = load_client_options_from_env(options)
        return await cls.create(signer, opts)

    def on(
        self,
        event: str,
        handler: EventHandler | None = None,
    ) -> EventHandler | Callable[[EventHandler], EventHandler]:
        """Register an event handler."""

        if handler is None:

            def decorator(fn: EventHandler) -> EventHandler:
                self._handlers[event].append(fn)
                return fn

            return decorator

        self._handlers[event].append(handler)
        return handler

    def use(self, *middlewares: Middleware | list[Middleware]) -> Agent:
        """Register middleware for message handling."""

        for middleware in middlewares:
            if isinstance(middleware, list):
                self._middlewares.extend(middleware)
            else:
                self._middlewares.append(middleware)
        return self

    @property
    def errors(self) -> _ErrorRegistrar:
        """Return an object to register error middleware."""

        return self._errors

    @property
    def client(self) -> Client:
        return self._client

    async def start(self) -> None:
        """Start the agent."""

        if self._running:
            return
        self._running = True

        await self._emit("start", ClientContext(self._client))

        self._conversation_stream = asyncio.create_task(self._consume_conversations())
        self._message_stream = asyncio.create_task(self._consume_messages())

    async def stop(self) -> None:
        """Stop the agent."""

        self._running = False
        await self._stop_streams()
        await self._emit("stop", ClientContext(self._client))

    async def _stop_streams(self) -> None:
        if self._conversation_stream_handle is not None:
            await self._conversation_stream_handle.close()
            self._conversation_stream_handle = None
        if self._message_stream_handle is not None:
            await self._message_stream_handle.close()
            self._message_stream_handle = None
        tasks = [task for task in (self._conversation_stream, self._message_stream) if task]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._conversation_stream = None
        self._message_stream = None

    async def _consume_conversations(self) -> None:
        try:
            stream: AsyncStream[Conversation | NativeBindings.FfiSubscribeError] = (
                self._client.conversations.stream()
            )
            self._conversation_stream_handle = stream
            async for item in stream:
                if not self._running:
                    break
                if isinstance(item, NativeBindings.FfiSubscribeError):
                    raise AgentStreamingError(str(item))  # pragma: no cover
                await self._handle_conversation(item)
        except asyncio.CancelledError:
            return
        except Exception as error:
            await self._handle_stream_error(error)
        finally:
            if self._conversation_stream_handle is not None:
                await self._conversation_stream_handle.close()
                self._conversation_stream_handle = None

    async def _consume_messages(self) -> None:
        try:
            stream: AsyncStream[DecodedMessage[object] | NativeBindings.FfiSubscribeError] = (
                self._client.conversations.stream_all_messages()
            )
            self._message_stream_handle = stream
            async for item in stream:
                if not self._running:
                    break
                if isinstance(item, NativeBindings.FfiSubscribeError):
                    raise AgentStreamingError(str(item))  # pragma: no cover
                await self._handle_message(item)
        except asyncio.CancelledError:
            return
        except Exception as error:
            await self._handle_stream_error(error)
        finally:
            if self._message_stream_handle is not None:
                await self._message_stream_handle.close()
                self._message_stream_handle = None

    async def _handle_stream_error(self, error: Exception) -> None:
        await self._stop_streams()
        recovered = await self._run_error_chain(error, ClientContext(self._client))
        if recovered:
            self._running = False
            await self.start()

    async def _handle_conversation(self, conversation: Conversation) -> None:
        context = ConversationContext(conversation, self._client)
        await self._emit("conversation", context)
        if isinstance(conversation, Dm):
            await self._emit("dm", context)
        elif isinstance(conversation, Group):
            await self._emit("group", context)

    async def _handle_message(self, message: DecodedMessage[object]) -> None:
        if not has_content(message):
            return
        if from_self(message, self._client):
            return

        conversation = await self._client.conversations.get_conversation_by_id(
            message.conversation_id
        )
        if conversation is None:
            raise AgentError(
                f"Failed to process message {message.id.hex()} for conversation "
                f"{message.conversation_id.hex()}: conversation not found."
            )

        context = MessageContext(message, conversation, self._client)
        topic = self._topic_for_message(message)
        await self._run_middleware_chain(context, topic)

    def _topic_for_message(self, message: DecodedMessage[object]) -> str:
        if is_text(message):
            return "text"
        if is_markdown(message):
            return "markdown"
        if is_reaction(message):
            return "reaction"
        if is_reply(message):
            return "reply"
        if is_remote_attachment(message):
            return "attachment"
        if is_read_receipt(message):
            return "read-receipt"
        if is_group_update(message):
            return "group-update"
        if is_transaction_reference(message):
            return "transaction-reference"
        if is_wallet_send_calls(message):
            return "wallet-send-calls"
        return "unknown_message"

    async def _run_middleware_chain(self, context: MessageContext, topic: str) -> None:
        async def final_emit() -> None:
            try:
                await self._emit(topic, context)
                await self._emit("message", context)
            except Exception as error:
                await self._run_error_chain(error, context)

        def wrap(
            middleware: Middleware,
            next_handler: Callable[[], Awaitable[None]],
        ) -> Callable[[], Awaitable[None]]:
            async def _wrapped() -> None:
                try:
                    await middleware(context, next_handler)
                except Exception as error:
                    resume = await self._run_error_chain(error, context)
                    if resume:
                        await next_handler()

            return _wrapped

        next_handler: Callable[[], Awaitable[None]] = final_emit
        for middleware in reversed(self._middlewares):
            next_handler = wrap(middleware, next_handler)

        await next_handler()

    async def _run_error_handler(
        self,
        handler: ErrorMiddleware,
        context: MessageContext | ClientContext,
        error: Exception,
    ) -> tuple[str, Exception | None]:
        settled = False
        outcome = "stopped"
        next_error: Exception | None = None

        async def next_handler(next_exc: Exception | None = None) -> None:
            nonlocal settled, outcome, next_error
            if settled:
                return
            settled = True
            if next_exc is None:
                outcome = "handled"
            else:
                outcome = "continue"
                next_error = next_exc

        try:
            result = handler(error, context, next_handler)
            if inspect.isawaitable(result):
                await result
        except Exception as exc:  # pragma: no cover - defensive
            if not settled:
                return "continue", exc
        return outcome, next_error

    async def _run_error_chain(
        self,
        error: Exception,
        context: MessageContext | ClientContext,
    ) -> bool:
        chain = [*self._error_middlewares, self._default_error_handler]
        current_error: Exception = error

        for handler in chain:
            outcome, next_error = await self._run_error_handler(handler, context, current_error)
            if outcome == "handled":
                return True
            if outcome == "stopped":
                return False
            if outcome == "continue" and next_error is not None:  # pragma: no branch
                current_error = next_error
        return False

    async def _default_error_handler(
        self,
        error: Exception,
        context: MessageContext | ClientContext,
        next_handler: Callable[[Exception | None], Awaitable[None]],
    ) -> None:
        await self._emit("unhandled_error", error)

    async def _emit(self, event: str, arg: EventPayload) -> None:
        handlers = self._handlers.get(event, [])
        for handler in handlers:
            result = handler(arg)
            if inspect.isawaitable(result):
                await result
