from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import pytest

from xmtp.conversations import Conversations, ListConversationsOptions, _default_list_options
from xmtp.conversation import Dm, Group
from xmtp.errors import ClientNotInitializedError
from xmtp.identifiers import Identifier, IdentifierKind


@dataclass
class _ConversationItem:
    conv: Any

    def conversation(self) -> Any:
        return self.conv


class _FakeConversation:
    def __init__(self, convo_type: Any, conversation_id: bytes = b'cid') -> None:
        self._type = convo_type
        self._id = conversation_id

    def conversation_type(self) -> Any:
        return self._type

    def id(self) -> bytes:
        return self._id


class _FakeCloser:
    def __init__(self) -> None:
        self.closed = False

    async def end_and_wait(self) -> None:
        self.closed = True


class _FakeConversations:
    def __init__(self, dm: _FakeConversation, group: _FakeConversation) -> None:
        self.dm = dm
        self.group = group
        self.callback = None
        self.message_callback = None
        self.synced = False
        self.synced_all = False
        self.synced_all_consents = None

    async def find_or_create_dm(self, identifier: Any, options: Any) -> Any:
        self.last_dm_identifier = identifier
        return self.dm

    async def create_group(self, identifiers: list[Any], options: Any) -> Any:
        self.last_group_identifiers = identifiers
        return self.group

    def list(self, options: Any) -> list[Any]:
        return [_ConversationItem(self.dm), _ConversationItem(self.group)]

    def list_dms(self, options: Any) -> list[Any]:
        return [_ConversationItem(self.dm)]

    def list_groups(self, options: Any) -> list[Any]:
        return [_ConversationItem(self.group)]

    async def stream(self, callback: Any) -> _FakeCloser:
        self.callback = callback
        self.stream_closer = _FakeCloser()
        return self.stream_closer

    async def stream_all_messages(self, callback: Any, _):
        self.message_callback = callback
        self.message_stream_closer = _FakeCloser()
        return self.message_stream_closer

    async def sync(self) -> None:
        self.synced = True

    async def sync_all_conversations(self, consent_states: Any = None) -> None:
        self.synced_all = True
        self.synced_all_consents = consent_states


class _FakeClient:
    def __init__(self, ffi_client: Any) -> None:
        self._client = ffi_client

    def _decode_message(self, message: Any) -> Any:
        return f'decoded:{message.id}'


class _FakeFfiClient:
    def __init__(self, conversation: Any) -> None:
        self._conversation = conversation

    def conversation(self, conversation_id: bytes) -> Any:
        if conversation_id == b'boom':
            raise RuntimeError('bad')
        return self._conversation


@pytest.mark.asyncio
async def test_list_conversations_options(fake_bindings) -> None:
    options = ListConversationsOptions(
        created_after_ns=1,
        created_before_ns=2,
        last_activity_after_ns=3,
        last_activity_before_ns=4,
        order_by=fake_bindings.FfiGroupQueryOrderBy.CREATED_AT,
        limit=10,
        consent_states=[fake_bindings.FfiConsentState.ALLOWED],
        include_duplicate_dms=True,
    )
    ffi = options.to_ffi()
    assert ffi.include_duplicate_dms is True
    assert ffi.limit == 10


def test_default_list_options(fake_bindings) -> None:
    ffi = _default_list_options()
    assert isinstance(ffi, fake_bindings.FfiListConversationsOptions)


@pytest.mark.asyncio
async def test_conversations_new_dm_and_group(fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    group = _FakeConversation(fake_bindings.FfiConversationType.GROUP)
    ffi = _FakeConversations(dm, group)
    client = _FakeClient(ffi)
    conversations = Conversations(client, ffi)

    dm_result = await conversations.new_dm('0xabc')
    assert isinstance(dm_result, Dm)
    assert ffi.last_dm_identifier.identifier == '0xabc'

    group_result = await conversations.new_group(['0xabc'])
    assert isinstance(group_result, Group)
    assert len(ffi.last_group_identifiers) == 1


@pytest.mark.asyncio
async def test_conversations_list_methods(fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    group = _FakeConversation(fake_bindings.FfiConversationType.GROUP)
    ffi = _FakeConversations(dm, group)
    client = _FakeClient(ffi)
    conversations = Conversations(client, ffi)

    assert isinstance((await conversations.list())[0], Dm)
    assert isinstance((await conversations.list())[1], Group)
    assert isinstance((await conversations.list_dms())[0], Dm)
    assert isinstance((await conversations.list_groups())[0], Group)


@pytest.mark.asyncio
async def test_conversations_get_conversation_by_id(fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    ffi_client = _FakeFfiClient(dm)
    client = _FakeClient(ffi_client)
    conversations = Conversations(client, None)

    assert await conversations.get_conversation_by_id(b'boom') is None

    client._client = None
    assert await conversations.get_conversation_by_id(b'ok') is None

    conversations = Conversations(client, None)
    client._client = ffi_client
    result = await conversations.get_conversation_by_id(b'ok')
    assert isinstance(result, Dm)


@pytest.mark.asyncio
async def test_conversations_stream(fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    group = _FakeConversation(fake_bindings.FfiConversationType.GROUP)
    ffi = _FakeConversations(dm, group)
    client = _FakeClient(ffi)
    conversations = Conversations(client, ffi)

    stream = conversations.stream()
    await asyncio.sleep(0)
    assert ffi.callback is not None

    ffi.callback.on_conversation(dm)
    item = await asyncio.wait_for(stream.__anext__(), timeout=1)
    assert isinstance(item, Dm)

    error = fake_bindings.FfiSubscribeError('boom')
    ffi.callback.on_error(error)
    item = await asyncio.wait_for(stream.__anext__(), timeout=1)
    assert item is error

    ffi.callback.on_close()
    await asyncio.sleep(0)
    with pytest.raises(StopAsyncIteration):
        await stream.__anext__()

    await stream.close()
    assert ffi.stream_closer.closed is True


@pytest.mark.asyncio
async def test_conversations_stream_all_messages(fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    group = _FakeConversation(fake_bindings.FfiConversationType.GROUP)
    ffi = _FakeConversations(dm, group)

    class _Message:
        def __init__(self) -> None:
            self.id = b'msg'

    client = _FakeClient(ffi)
    conversations = Conversations(client, ffi)
    stream = conversations.stream_all_messages()
    await asyncio.sleep(0)
    assert ffi.message_callback is not None

    ffi.message_callback.on_message(_Message())
    item = await asyncio.wait_for(stream.__anext__(), timeout=1)
    assert item == 'decoded:b\'msg\''

    error = fake_bindings.FfiSubscribeError('boom')
    ffi.message_callback.on_error(error)
    item = await asyncio.wait_for(stream.__anext__(), timeout=1)
    assert item is error

    ffi.message_callback.on_close()
    await asyncio.sleep(0)
    with pytest.raises(StopAsyncIteration):
        await stream.__anext__()

    await stream.close()
    assert ffi.message_stream_closer.closed is True


@pytest.mark.asyncio
async def test_conversations_sync(fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    group = _FakeConversation(fake_bindings.FfiConversationType.GROUP)
    ffi = _FakeConversations(dm, group)
    client = _FakeClient(ffi)
    conversations = Conversations(client, ffi)

    await conversations.sync()
    await conversations.sync_all_conversations()
    await conversations.sync_all_conversations([fake_bindings.FfiConsentState.ALLOWED])
    assert ffi.synced is True
    assert ffi.synced_all is True
    assert ffi.synced_all_consents == [fake_bindings.FfiConsentState.ALLOWED]


@pytest.mark.asyncio
async def test_conversations_sync_signature_error(monkeypatch, fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    group = _FakeConversation(fake_bindings.FfiConversationType.GROUP)
    ffi = _FakeConversations(dm, group)
    client = _FakeClient(ffi)
    conversations = Conversations(client, ffi)

    def boom(_):
        raise TypeError('no signature')

    monkeypatch.setattr('xmtp.conversations.inspect.signature', boom)
    await conversations.sync_all_conversations()
    assert ffi.synced_all is True


@pytest.mark.asyncio
async def test_conversations_sync_no_arg_signature(fake_bindings) -> None:
    dm = _FakeConversation(fake_bindings.FfiConversationType.DM)
    group = _FakeConversation(fake_bindings.FfiConversationType.GROUP)

    class _NoArgConversations(_FakeConversations):
        async def sync_all_conversations(self) -> None:  # type: ignore[override]
            self.synced_all = True

    ffi = _NoArgConversations(dm, group)
    client = _FakeClient(ffi)
    conversations = Conversations(client, ffi)

    await conversations.sync_all_conversations()
    assert ffi.synced_all is True


@pytest.mark.asyncio
async def test_conversations_requires_client(fake_bindings) -> None:
    conversations = Conversations(object(), None)
    with pytest.raises(ClientNotInitializedError):
        await conversations.list_dms()
