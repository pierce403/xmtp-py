from __future__ import annotations

import pytest

from xmtp_agent.test_utils import (
    MockAsyncStream,
    create_mock_message,
    flush_asyncio,
    record_messages,
    replay_messages,
    serialize_message,
)
from xmtp_content_type_text import ContentTypeText


def test_create_mock_message_defaults() -> None:
    message = create_mock_message('hello')
    assert message.content == 'hello'
    assert message.content_type_id == str(ContentTypeText)
    assert message.id == b'mock-message-id'
    assert message.conversation_id == b'test-conversation-id'


@pytest.mark.asyncio
async def test_mock_async_stream_iterates() -> None:
    stream = MockAsyncStream([1, 2])
    stream.end()
    items = [item async for item in stream]
    assert items == [1, 2]


@pytest.mark.asyncio
async def test_mock_async_stream_push_and_close() -> None:
    stream = MockAsyncStream[int]()
    stream.push(3)
    await stream.close()
    items = [item async for item in stream]
    assert items == [3]


@pytest.mark.asyncio
async def test_record_and_replay_messages() -> None:
    messages = [
        create_mock_message('one'),
        create_mock_message('two'),
    ]
    stream = MockAsyncStream(messages)
    stream.end()
    records = await record_messages(stream)
    replayed = replay_messages(records)
    items = [serialize_message(item) async for item in replayed]
    assert items == records


@pytest.mark.asyncio
async def test_record_messages_limit() -> None:
    messages = [
        create_mock_message('one'),
        create_mock_message('two'),
    ]
    stream = MockAsyncStream(messages)
    stream.end()
    records = await record_messages(stream, limit=1)
    assert len(records) == 1


@pytest.mark.asyncio
async def test_flush_asyncio() -> None:
    await flush_asyncio()
