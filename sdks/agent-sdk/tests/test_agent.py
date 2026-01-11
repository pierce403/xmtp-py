from __future__ import annotations

import asyncio
import types
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest

from xmtp.messages import DecodedMessage
from xmtp_agent.agent import Agent
from xmtp_agent.context import MessageContext
from xmtp_agent.errors import AgentError
from xmtp.types import ClientOptions, LogLevel
from xmtp_content_type_group_updated import ContentTypeGroupUpdated
from xmtp_content_type_markdown import ContentTypeMarkdown
from xmtp_content_type_reaction import ContentTypeReaction
from xmtp_content_type_read_receipt import ContentTypeReadReceipt
from xmtp_content_type_remote_attachment import ContentTypeRemoteAttachment
from xmtp_content_type_reply import ContentTypeReply
from xmtp_content_type_text import ContentTypeText
from xmtp_content_type_transaction_reference import ContentTypeTransactionReference
from xmtp_content_type_wallet_send_calls import ContentTypeWalletSendCalls


class _FakeStream:
    def __init__(self, items: list[Any]) -> None:
        self._items = list(items)
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._items:
            return self._items.pop(0)
        raise StopAsyncIteration

    async def close(self) -> None:
        self.closed = True


class _CancelStream(_FakeStream):
    async def __anext__(self):
        raise asyncio.CancelledError


class _FakeConversation:
    def __init__(self) -> None:
        self.sent: list[tuple[Any, Any | None]] = []

    async def send(self, content: Any, content_type: Any | None = None) -> None:
        self.sent.append((content, content_type))


class _FakeConversations:
    def __init__(self, conversation_stream: _FakeStream, message_stream: _FakeStream, conversation: Any) -> None:
        self._conversation_stream = conversation_stream
        self._message_stream = message_stream
        self._conversation = conversation

    def stream(self):
        return self._conversation_stream

    def stream_all_messages(self):
        return self._message_stream

    async def get_conversation_by_id(self, conversation_id: bytes):
        return self._conversation


class _FakeClient:
    def __init__(self, conversations: _FakeConversations) -> None:
        self.conversations = conversations
        self.inbox_id = 'self-inbox'
        self.options = type('Options', (), {'env': 'dev'})()


@dataclass
class _MessageFactory:
    content_type_id: str
    content: Any
    sender_inbox_id: str = 'sender'

    def build(self) -> DecodedMessage[Any]:
        return DecodedMessage(
            id=b'id',
            conversation_id=b'cid',
            sender_inbox_id=self.sender_inbox_id,
            sent_at=datetime.now(timezone.utc),
            content=self.content,
            content_type_id=self.content_type_id,
        )


@pytest.mark.asyncio
async def test_agent_start_stop(fake_bindings) -> None:
    conversation_stream = _FakeStream([])
    message_stream = _FakeStream([])
    conversations = _FakeConversations(conversation_stream, message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    started = False
    stopped = False

    @agent.on('start')
    async def _on_start(_ctx) -> None:
        nonlocal started
        started = True

    @agent.on('stop')
    async def _on_stop(_ctx) -> None:
        nonlocal stopped
        stopped = True

    await agent.start()
    await asyncio.sleep(0)
    await agent.stop()

    assert started is True
    assert stopped is True
    assert conversation_stream.closed is True
    assert message_stream.closed is True


@pytest.mark.asyncio
async def test_agent_start_noop_when_running(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True
    await agent.start()
    assert agent._running is True


@pytest.mark.asyncio
async def test_agent_stop_streams_closes_handles(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    class _Handle:
        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    conv_handle = _Handle()
    msg_handle = _Handle()
    agent._conversation_stream_handle = conv_handle
    agent._message_stream_handle = msg_handle
    agent._conversation_stream = asyncio.create_task(asyncio.sleep(0))
    agent._message_stream = asyncio.create_task(asyncio.sleep(0))

    await agent._stop_streams()

    assert conv_handle.closed is True
    assert msg_handle.closed is True
    assert agent._conversation_stream_handle is None
    assert agent._message_stream_handle is None


@pytest.mark.asyncio
async def test_agent_create_defaults(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_create(cls, _signer, options):
        captured['options'] = options
        conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
        return _FakeClient(conversations)

    monkeypatch.setattr('xmtp_agent.agent.Client.create', classmethod(fake_create))

    agent = await Agent.create(object(), ClientOptions())
    assert isinstance(agent, Agent)
    assert captured['options'].app_version == 'agent-sdk/alpha'
    assert captured['options'].disable_device_sync is True


@pytest.mark.asyncio
async def test_agent_create_debug_env(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_create(cls, _signer, options):
        captured['options'] = options
        conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
        return _FakeClient(conversations)

    monkeypatch.setenv('XMTP_FORCE_DEBUG', '1')
    monkeypatch.setenv('XMTP_FORCE_DEBUG_LEVEL', 'debug')
    monkeypatch.setattr('xmtp_agent.agent.Client.create', classmethod(fake_create))

    agent = await Agent.create(object(), ClientOptions())
    assert isinstance(agent, Agent)
    assert captured['options'].debug_events_enabled is True
    assert captured['options'].structured_logging is True
    assert captured['options'].logging_level == LogLevel.DEBUG


@pytest.mark.asyncio
async def test_agent_create_preserves_options_invalid_debug(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_create(cls, _signer, options):
        captured['options'] = options
        conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
        return _FakeClient(conversations)

    monkeypatch.setenv('XMTP_FORCE_DEBUG', '1')
    monkeypatch.setenv('XMTP_FORCE_DEBUG_LEVEL', 'invalid')
    monkeypatch.setattr('xmtp_agent.agent.Client.create', classmethod(fake_create))

    options = ClientOptions(app_version='custom', disable_device_sync=True)
    agent = await Agent.create(object(), options)
    assert isinstance(agent, Agent)
    assert captured['options'].app_version == 'custom'
    assert captured['options'].disable_device_sync is True
    assert captured['options'].logging_level == LogLevel.WARN


@pytest.mark.asyncio
async def test_agent_create_from_env(monkeypatch) -> None:
    async def fake_create(cls, _signer, options):
        conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
        return _FakeClient(conversations)

    monkeypatch.setattr('xmtp_agent.agent.load_signer_from_env', lambda: object())
    monkeypatch.setattr('xmtp_agent.agent.load_client_options_from_env', lambda opts=None: ClientOptions())
    monkeypatch.setattr('xmtp_agent.agent.Client.create', classmethod(fake_create))

    agent = await Agent.create_from_env()
    assert isinstance(agent, Agent)


@pytest.mark.asyncio
async def test_agent_handle_message_dispatch(fake_bindings) -> None:
    conversation = _FakeConversation()
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), conversation)
    agent = Agent(_FakeClient(conversations))

    handled = False

    @agent.on('text')
    async def _on_text(ctx: MessageContext) -> None:
        nonlocal handled
        handled = True
        await ctx.send_text('reply')

    message = _MessageFactory(content_type_id=str(ContentTypeText), content='hi').build()
    await agent._handle_message(message)

    assert handled is True
    assert conversation.sent[0] == ('reply', None)


@pytest.mark.asyncio
async def test_agent_handle_message_filters_out(fake_bindings) -> None:
    conversation = _FakeConversation()
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), conversation)
    agent = Agent(_FakeClient(conversations))

    handled = False

    @agent.on('message')
    async def _on_message(_ctx) -> None:
        nonlocal handled
        handled = True

    message = _MessageFactory(content_type_id=str(ContentTypeText), content=None).build()
    await agent._handle_message(message)
    assert handled is False

    message = _MessageFactory(
        content_type_id=str(ContentTypeText),
        content='hi',
        sender_inbox_id='self-inbox',
    ).build()
    await agent._handle_message(message)
    assert handled is False


@pytest.mark.asyncio
async def test_agent_handle_message_missing_conversation(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), None)
    agent = Agent(_FakeClient(conversations))
    message = _MessageFactory(content_type_id=str(ContentTypeText), content='hi').build()

    with pytest.raises(AgentError, match='conversation not found'):
        await agent._handle_message(message)


@pytest.mark.asyncio
async def test_agent_topic_for_message(fake_bindings) -> None:
    agent = Agent(_FakeClient(_FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())))
    assert agent._topic_for_message(_MessageFactory(str(ContentTypeText), 'hi').build()) == 'text'
    assert agent._topic_for_message(_MessageFactory(str(ContentTypeMarkdown), 'md').build()) == 'markdown'
    assert agent._topic_for_message(_MessageFactory(str(ContentTypeReaction), {}).build()) == 'reaction'
    assert agent._topic_for_message(_MessageFactory(str(ContentTypeReply), {}).build()) == 'reply'
    assert agent._topic_for_message(_MessageFactory(str(ContentTypeRemoteAttachment), {}).build()) == 'attachment'
    assert agent._topic_for_message(_MessageFactory(str(ContentTypeReadReceipt), {}).build()) == 'read-receipt'
    assert agent._topic_for_message(_MessageFactory(str(ContentTypeGroupUpdated), {}).build()) == 'group-update'
    assert (
        agent._topic_for_message(_MessageFactory(str(ContentTypeTransactionReference), {}).build())
        == 'transaction-reference'
    )
    assert (
        agent._topic_for_message(_MessageFactory(str(ContentTypeWalletSendCalls), {}).build())
        == 'wallet-send-calls'
    )
    assert agent._topic_for_message(_MessageFactory('unknown', {}).build()) == 'unknown_message'


@pytest.mark.asyncio
async def test_agent_handle_conversation_events(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    events: list[str] = []

    agent.on('conversation', lambda _ctx: events.append('conversation'))
    agent.on('dm', lambda _ctx: events.append('dm'))
    agent.on('group', lambda _ctx: events.append('group'))

    from xmtp.conversation import Dm, Group

    await agent._handle_conversation(Dm(object(), object()))
    await agent._handle_conversation(Group(object(), object()))

    assert events == ['conversation', 'dm', 'conversation', 'group']


@pytest.mark.asyncio
async def test_agent_handle_conversation_unknown(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    events: list[str] = []

    agent.on('conversation', lambda _ctx: events.append('conversation'))
    agent.on('dm', lambda _ctx: events.append('dm'))
    agent.on('group', lambda _ctx: events.append('group'))

    await agent._handle_conversation(object())
    assert events == ['conversation']


@pytest.mark.asyncio
async def test_agent_middleware_and_error_chain(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    calls: list[str] = []

    async def middleware(ctx, next_handler):
        calls.append('before')
        await next_handler()
        calls.append('after')

    async def error_middleware(error, ctx, next_handler):
        calls.append('error')
        await next_handler(None)

    agent.use(middleware)
    agent.errors.use(error_middleware)

    @agent.on('text')
    async def _on_text(_ctx):
        calls.append('handler')

    agent.on('text', lambda _ctx: calls.append('sync'))

    message = _MessageFactory(content_type_id=str(ContentTypeText), content='hi').build()
    await agent._handle_message(message)

    assert calls == ['before', 'handler', 'sync', 'after']


@pytest.mark.asyncio
async def test_agent_middleware_error_resume(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    calls: list[str] = []

    async def middleware(_ctx, _next_handler):
        raise RuntimeError('boom')

    async def error_middleware(error, ctx, next_handler):
        calls.append('error')
        await next_handler(None)

    agent.use(middleware)
    agent.errors.use(error_middleware)

    @agent.on('text')
    async def _on_text(_ctx):
        calls.append('handler')

    message = _MessageFactory(content_type_id=str(ContentTypeText), content='hi').build()
    await agent._handle_message(message)

    assert calls == ['error', 'handler']


@pytest.mark.asyncio
async def test_agent_middleware_error_no_resume(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    calls: list[str] = []

    async def middleware(_ctx, _next_handler):
        raise RuntimeError('boom')

    async def error_middleware(_error, _ctx, _next_handler):
        calls.append('error')

    agent.use(middleware)
    agent.errors.use(error_middleware)

    @agent.on('text')
    async def _on_text(_ctx):
        calls.append('handler')

    message = _MessageFactory(content_type_id=str(ContentTypeText), content='hi').build()
    await agent._handle_message(message)

    assert calls == ['error']


@pytest.mark.asyncio
async def test_agent_error_chain_outcomes(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    async def handler_handles(error, ctx, next_handler):
        await next_handler(None)

    async def handler_stops(error, ctx, next_handler):
        return None

    async def handler_continue(error, ctx, next_handler):
        await next_handler(RuntimeError('next'))

    agent._error_middlewares = [handler_handles]
    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is True

    agent._error_middlewares = [handler_stops]
    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is False

    def handler_sync(error, ctx, next_handler):
        return None

    agent._error_middlewares = [handler_sync]
    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is False

    seen: list[str] = []

    async def handler_capture(error, ctx, next_handler):
        seen.append(str(error))
        await next_handler(None)

    agent._error_middlewares = [handler_continue, handler_capture]
    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is True
    assert seen == ['next']


@pytest.mark.asyncio
async def test_agent_error_chain_continue_updates_error(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    seen: list[str] = []

    async def handler_continue(_error, _ctx, next_handler):
        await next_handler(RuntimeError('next-error'))

    async def handler_capture(error, _ctx, next_handler):
        seen.append(str(error))
        await next_handler(None)

    agent._error_middlewares = [handler_continue, handler_capture]
    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is True
    assert seen == ['next-error']


@pytest.mark.asyncio
async def test_agent_error_chain_final_continue_returns_false(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    async def handler_continue(_error, _ctx, next_handler):
        await next_handler(RuntimeError('next'))

    async def final_continue(_error, _ctx, next_handler):
        await next_handler(RuntimeError('final'))

    agent._error_middlewares = [handler_continue]
    agent._default_error_handler = final_continue  # type: ignore[assignment]
    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is False


@pytest.mark.asyncio
async def test_agent_error_chain_continue_branch(fake_bindings, monkeypatch) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    calls: list[str] = []

    async def fake_run_error_handler(_handler, _context, error):
        calls.append(str(error))
        if len(calls) == 1:
            return 'continue', RuntimeError('next')
        return 'handled', None

    monkeypatch.setattr(agent, '_run_error_handler', fake_run_error_handler)
    agent._error_middlewares = [lambda *_args, **_kwargs: None]
    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is True
    assert calls == ['boom', 'next']


@pytest.mark.asyncio
async def test_agent_error_handler_settled_guard(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    async def handler(_error, _ctx, next_handler):
        await next_handler(None)
        await next_handler(RuntimeError('ignored'))

    outcome, next_error = await agent._run_error_handler(handler, MessageContext, RuntimeError('boom'))
    assert outcome == 'handled'
    assert next_error is None


@pytest.mark.asyncio
async def test_agent_default_error_handler_emits(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    seen: list[str] = []

    @agent.on('unhandled_error')
    async def _on_error(error):
        seen.append(str(error))

    assert await agent._run_error_chain(RuntimeError('boom'), MessageContext) is False
    assert seen == ['boom']

@pytest.mark.asyncio
async def test_agent_stream_error_handling(fake_bindings, monkeypatch) -> None:
    error_item = fake_bindings.FfiSubscribeError('boom')
    conversation_stream = _FakeStream([error_item])
    message_stream = _FakeStream([])
    conversations = _FakeConversations(conversation_stream, message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    handled: list[Exception] = []

    async def _handle_stream_error(error: Exception) -> None:
        handled.append(error)

    monkeypatch.setattr(agent, '_handle_stream_error', _handle_stream_error)
    await agent.start()
    await asyncio.sleep(0)

    assert handled


@pytest.mark.asyncio
async def test_agent_message_stream_error_handling(fake_bindings, monkeypatch) -> None:
    error_item = fake_bindings.FfiSubscribeError('boom')
    conversation_stream = _FakeStream([])
    message_stream = _FakeStream([error_item])
    conversations = _FakeConversations(conversation_stream, message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    handled: list[Exception] = []

    async def _handle_stream_error(error: Exception) -> None:
        handled.append(error)

    monkeypatch.setattr(agent, '_handle_stream_error', _handle_stream_error)
    await agent.start()
    await asyncio.sleep(0)

    assert handled


def test_agent_use_list(fake_bindings) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    async def middleware(ctx, next_handler):
        await next_handler()

    async def error_middleware(error, ctx, next_handler):
        await next_handler(None)

    agent.use([middleware])
    agent.errors.use([error_middleware])
    assert agent is not None


@pytest.mark.asyncio
async def test_agent_handle_stream_error_restarts(fake_bindings, monkeypatch) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    async def fake_run_error_chain(error, context):
        return True

    called = {'start': 0}

    async def fake_start():
        called['start'] += 1

    monkeypatch.setattr(agent, '_run_error_chain', fake_run_error_chain)
    monkeypatch.setattr(agent, 'start', fake_start)

    await agent._handle_stream_error(RuntimeError('boom'))
    assert called['start'] == 1


@pytest.mark.asyncio
async def test_agent_handle_stream_error_stops(fake_bindings, monkeypatch) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))

    async def fake_run_error_chain(error, context):
        return False

    monkeypatch.setattr(agent, '_run_error_chain', fake_run_error_chain)
    await agent._handle_stream_error(RuntimeError('boom'))


@pytest.mark.asyncio
async def test_agent_run_middleware_chain_emitter_error(fake_bindings, monkeypatch) -> None:
    conversations = _FakeConversations(_FakeStream([]), _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    called: list[str] = []

    @agent.on('text')
    async def _on_text(_ctx):
        raise RuntimeError('boom')

    async def fake_run_error_chain(error, ctx):
        called.append(str(error))
        return False

    monkeypatch.setattr(agent, '_run_error_chain', fake_run_error_chain)

    message = _MessageFactory(content_type_id=str(ContentTypeText), content='hi').build()
    context = MessageContext(message, _FakeConversation(), agent.client)
    await agent._run_middleware_chain(context, 'text')
    assert called == ['boom']


@pytest.mark.asyncio
async def test_agent_consume_conversations_breaks_when_stopped(fake_bindings) -> None:
    conversation_stream = _FakeStream([object()])
    conversations = _FakeConversations(conversation_stream, _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = False
    await agent._consume_conversations()
    assert conversation_stream.closed is True
    assert agent._conversation_stream_handle is None


@pytest.mark.asyncio
async def test_agent_consume_conversations_handles_item(fake_bindings, monkeypatch) -> None:
    item = object()
    conversation_stream = _FakeStream([item])
    conversations = _FakeConversations(conversation_stream, _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True
    handled: list[object] = []

    async def _handle_conversation(conversation):
        handled.append(conversation)

    monkeypatch.setattr(agent, '_handle_conversation', _handle_conversation)
    await agent._consume_conversations()
    assert handled == [item]


@pytest.mark.asyncio
async def test_agent_consume_conversations_subscribe_error(fake_bindings, monkeypatch) -> None:
    import xmtp_agent.agent as agent_module

    patched_bindings = types.SimpleNamespace(FfiSubscribeError=object)
    monkeypatch.setattr(agent_module, 'NativeBindings', patched_bindings)
    monkeypatch.setitem(Agent._consume_conversations.__globals__, 'NativeBindings', patched_bindings)
    error_item = object()
    conversation_stream = _FakeStream([error_item])
    conversations = _FakeConversations(conversation_stream, _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True
    async def fake_run_error_chain(_error, _ctx):
        return False

    monkeypatch.setattr(agent, '_run_error_chain', fake_run_error_chain)

    handled: list[Exception] = []

    original_handle = agent._handle_stream_error

    async def wrapped_handle(error: Exception) -> None:
        handled.append(error)
        await original_handle(error)

    monkeypatch.setattr(agent, '_handle_stream_error', wrapped_handle)
    await agent._consume_conversations()
    assert handled
    assert agent._conversation_stream_handle is None


@pytest.mark.asyncio
async def test_agent_consume_conversations_cancelled(fake_bindings, monkeypatch) -> None:
    conversation_stream = _CancelStream([])
    conversations = _FakeConversations(conversation_stream, _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True
    called: list[str] = []

    async def _handle_stream_error(error: Exception) -> None:
        called.append(str(error))

    monkeypatch.setattr(agent, '_handle_stream_error', _handle_stream_error)
    await agent._consume_conversations()
    assert called == []


@pytest.mark.asyncio
async def test_agent_consume_messages_breaks_when_stopped(fake_bindings) -> None:
    message_stream = _FakeStream([object()])
    conversations = _FakeConversations(_FakeStream([]), message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = False
    await agent._consume_messages()
    assert message_stream.closed is True
    assert agent._message_stream_handle is None


@pytest.mark.asyncio
async def test_agent_consume_messages_handles_item(fake_bindings, monkeypatch) -> None:
    message = _MessageFactory(content_type_id=str(ContentTypeText), content='hi').build()
    message_stream = _FakeStream([message])
    conversations = _FakeConversations(_FakeStream([]), message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True
    handled: list[object] = []

    async def _handle_message(item):
        handled.append(item)

    monkeypatch.setattr(agent, '_handle_message', _handle_message)
    await agent._consume_messages()
    assert handled == [message]


@pytest.mark.asyncio
async def test_agent_consume_messages_subscribe_error(fake_bindings, monkeypatch) -> None:
    import xmtp_agent.agent as agent_module

    patched_bindings = types.SimpleNamespace(FfiSubscribeError=object)
    monkeypatch.setattr(agent_module, 'NativeBindings', patched_bindings)
    monkeypatch.setitem(Agent._consume_messages.__globals__, 'NativeBindings', patched_bindings)
    error_item = object()
    message_stream = _FakeStream([error_item])
    conversations = _FakeConversations(_FakeStream([]), message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True
    async def fake_run_error_chain(_error, _ctx):
        return False

    monkeypatch.setattr(agent, '_run_error_chain', fake_run_error_chain)

    handled: list[Exception] = []

    original_handle = agent._handle_stream_error

    async def wrapped_handle(error: Exception) -> None:
        handled.append(error)
        await original_handle(error)

    monkeypatch.setattr(agent, '_handle_stream_error', wrapped_handle)
    await agent._consume_messages()
    assert handled
    assert agent._message_stream_handle is None


@pytest.mark.asyncio
async def test_agent_consume_messages_cancelled(fake_bindings, monkeypatch) -> None:
    message_stream = _CancelStream([])
    conversations = _FakeConversations(_FakeStream([]), message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True
    called: list[str] = []

    async def _handle_stream_error(error: Exception) -> None:
        called.append(str(error))

    monkeypatch.setattr(agent, '_handle_stream_error', _handle_stream_error)
    await agent._consume_messages()
    assert called == []


@pytest.mark.asyncio
async def test_agent_consume_conversations_subscribe_error_real_bindings(monkeypatch) -> None:
    pytest.importorskip('xmtp_bindings')
    from xmtp.bindings import NativeBindings

    conversation_stream = _FakeStream([NativeBindings.FfiSubscribeError('boom')])
    conversations = _FakeConversations(conversation_stream, _FakeStream([]), _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True

    async def fake_run_error_chain(_error, _ctx):
        return False

    monkeypatch.setattr(agent, '_run_error_chain', fake_run_error_chain)
    await agent._consume_conversations()


@pytest.mark.asyncio
async def test_agent_consume_messages_subscribe_error_real_bindings(monkeypatch) -> None:
    pytest.importorskip('xmtp_bindings')
    from xmtp.bindings import NativeBindings

    message_stream = _FakeStream([NativeBindings.FfiSubscribeError('boom')])
    conversations = _FakeConversations(_FakeStream([]), message_stream, _FakeConversation())
    agent = Agent(_FakeClient(conversations))
    agent._running = True

    async def fake_run_error_chain(_error, _ctx):
        return False

    monkeypatch.setattr(agent, '_run_error_chain', fake_run_error_chain)
    await agent._consume_messages()
