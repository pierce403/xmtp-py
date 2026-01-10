from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest

from xmtp.conversation import Dm, Group
from xmtp.messages import DecodedMessage
from xmtp_agent.context import ClientContext, ConversationContext, MessageContext
from xmtp_content_type_markdown import ContentTypeMarkdown
from xmtp_content_type_reaction import ContentTypeReaction, Reaction
from xmtp_content_type_remote_attachment import ContentTypeRemoteAttachment, RemoteAttachment
from xmtp_content_type_reply import ContentTypeReply, Reply
from xmtp_content_type_text import ContentTypeText, TextCodec


class _FakeConversation:
    def __init__(self, consent_state: Any = None) -> None:
        self.sent: list[tuple[Any, Any | None]] = []
        self._consent_state = consent_state

    @property
    def consent_state(self) -> Any:
        return self._consent_state

    async def send(self, content: Any, content_type: Any | None = None) -> None:
        self.sent.append((content, content_type))


@dataclass
class _AccountIdentity:
    identifier: str


@dataclass
class _InboxState:
    account_identities: list[_AccountIdentity]


class _Preferences:
    def __init__(self, states: list[_InboxState]) -> None:
        self._states = states

    async def inbox_state_from_inbox_ids(self, inbox_ids, refresh_from_network=False):
        return self._states


class _Client:
    def __init__(self, preferences: _Preferences) -> None:
        self.preferences = preferences
        self.account_identifier = None
        self.options = type('Options', (), {'env': 'dev'})()


@pytest.mark.asyncio
async def test_conversation_context_send(fake_bindings) -> None:
    convo = _FakeConversation(consent_state=fake_bindings.FfiConsentState.ALLOWED)
    ctx = ConversationContext(conversation=convo, client=_Client(_Preferences([])))

    await ctx.send_text('hi')
    await ctx.send_markdown('md')
    await ctx.send_remote_attachment(RemoteAttachment(
        url='https://example',
        content_digest='digest',
        salt=b'salt',
        nonce=b'nonce',
        secret=b'secret',
        scheme='https',
        content_length=1,
        filename=None,
    ))

    assert ctx.is_allowed is True
    assert ctx.is_denied is False
    assert ctx.is_unknown is False

    assert convo.sent[0] == ('hi', None)
    assert convo.sent[1] == ('md', ContentTypeMarkdown)
    assert convo.sent[2][1] == ContentTypeRemoteAttachment


def test_conversation_context_type_helpers() -> None:
    dm = Dm(object(), object())
    group = Group(object(), object())
    assert ConversationContext(conversation=dm, client=_Client(_Preferences([]))).is_dm() is True
    assert ConversationContext(conversation=group, client=_Client(_Preferences([]))).is_group() is True


def test_conversation_context_consent_states(fake_bindings) -> None:
    convo = _FakeConversation(consent_state=fake_bindings.FfiConsentState.DENIED)
    ctx = ConversationContext(conversation=convo, client=_Client(_Preferences([])))
    assert ctx.is_denied is True
    assert ctx.is_allowed is False
    assert ctx.is_unknown is False

    convo = _FakeConversation(consent_state=fake_bindings.FfiConsentState.UNKNOWN)
    ctx = ConversationContext(conversation=convo, client=_Client(_Preferences([])))
    assert ctx.is_unknown is True


@pytest.mark.asyncio
async def test_message_context_helpers(fake_bindings) -> None:
    message = DecodedMessage(
        id=b'id',
        conversation_id=b'cid',
        sender_inbox_id='sender',
        sent_at=datetime.now(timezone.utc),
        content='hello',
        content_type_id=str(ContentTypeText),
    )
    convo = _FakeConversation()
    client = _Client(_Preferences([]))
    ctx = MessageContext(message=message, conversation=convo, client=client)

    assert ctx.is_text() is True
    assert ctx.is_markdown() is False
    assert ctx.uses_codec(TextCodec) is True

    await ctx.send_text_reply('reply')
    await ctx.send_markdown_reply('md')
    await ctx.send_reaction(':)')

    assert convo.sent[0][1] == ContentTypeReply
    assert isinstance(convo.sent[0][0], Reply)
    assert convo.sent[0][0].content == 'reply'
    assert convo.sent[0][0].content_type == ContentTypeText

    assert convo.sent[1][1] == ContentTypeReply
    assert isinstance(convo.sent[1][0], Reply)
    assert convo.sent[1][0].content == 'md'
    assert convo.sent[1][0].content_type == ContentTypeMarkdown

    assert isinstance(convo.sent[2][0], Reaction)
    assert convo.sent[2][1] == ContentTypeReaction


def test_message_context_predicates() -> None:
    message = DecodedMessage(
        id=b'id',
        conversation_id=b'cid',
        sender_inbox_id='sender',
        sent_at=datetime.now(timezone.utc),
        content='reply',
        content_type_id=str(ContentTypeReply),
    )
    ctx = MessageContext(message=message, conversation=_FakeConversation(), client=_Client(_Preferences([])))
    assert ctx.is_reply() is True
    assert ctx.is_reaction() is False

    message = DecodedMessage(
        id=b'id',
        conversation_id=b'cid',
        sender_inbox_id='sender',
        sent_at=datetime.now(timezone.utc),
        content='md',
        content_type_id=str(ContentTypeMarkdown),
    )
    ctx = MessageContext(message=message, conversation=_FakeConversation(), client=_Client(_Preferences([])))
    assert ctx.is_markdown() is True

    message = DecodedMessage(
        id=b'id',
        conversation_id=b'cid',
        sender_inbox_id='sender',
        sent_at=datetime.now(timezone.utc),
        content='attachment',
        content_type_id=str(ContentTypeRemoteAttachment),
    )
    ctx = MessageContext(message=message, conversation=_FakeConversation(), client=_Client(_Preferences([])))
    assert ctx.is_remote_attachment() is True

    message = DecodedMessage(
        id=b'id',
        conversation_id=b'cid',
        sender_inbox_id='sender',
        sent_at=datetime.now(timezone.utc),
        content='reaction',
        content_type_id=str(ContentTypeReaction),
    )
    ctx = MessageContext(message=message, conversation=_FakeConversation(), client=_Client(_Preferences([])))
    assert ctx.is_reaction() is True


@pytest.mark.asyncio
async def test_message_context_get_sender_address(fake_bindings) -> None:
    message = DecodedMessage(
        id=b'id',
        conversation_id=b'cid',
        sender_inbox_id='sender',
        sent_at=datetime.now(timezone.utc),
        content='hello',
        content_type_id=str(ContentTypeText),
    )

    preferences = _Preferences([_InboxState([_AccountIdentity('0xabc')])])
    client = _Client(preferences)
    ctx = MessageContext(message=message, conversation=_FakeConversation(), client=client)
    assert await ctx.get_sender_address() == '0xabc'

    preferences = _Preferences([])
    client = _Client(preferences)
    ctx = MessageContext(message=message, conversation=_FakeConversation(), client=client)
    assert await ctx.get_sender_address() is None

    preferences = _Preferences([_InboxState([])])
    client = _Client(preferences)
    ctx = MessageContext(message=message, conversation=_FakeConversation(), client=client)
    assert await ctx.get_sender_address() is None


def test_client_context() -> None:
    client = _Client(_Preferences([]))
    ctx = ClientContext(client)
    assert ctx.client is client
    assert ctx.get_client_address() is None

    client.account_identifier = type('Identifier', (), {'value': '0xabc'})()
    assert ctx.get_client_address() == '0xabc'
