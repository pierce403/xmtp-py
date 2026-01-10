from __future__ import annotations

import asyncio
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
