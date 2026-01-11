from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from xmtp.conversation import Conversation, Dm, Group
from xmtp.errors import MissingContentTypeError
from xmtp.identifiers import Identifier, IdentifierKind


@dataclass
class _Member:
    inbox_id: str


class _FakeFfiConversation:
    def __init__(self) -> None:
        self.sent_text: str | None = None
        self.sent_payload: bytes | None = None
        self.sent_opts: Any | None = None
        self.peer_inbox = 'peer'
        self._consent_state = 'allowed'
        self.members_added: list[str] | None = None
        self.members_removed: list[str] | None = None
        self.admin_added: str | None = None
        self.admin_removed: str | None = None

    def id(self) -> bytes:
        return b'cid'

    def consent_state(self) -> str:
        return self._consent_state

    async def update_consent_state(self, state: Any) -> None:
        self._consent_state = state

    async def send_text(self, content: str) -> bytes:
        self.sent_text = content
        return b'msg-id'

    async def send(self, payload: bytes, opts: Any) -> bytes:
        self.sent_payload = payload
        self.sent_opts = opts
        return b'msg-id'

    def dm_peer_inbox_id(self) -> str:
        return self.peer_inbox

    async def add_members_by_inbox_id(self, inbox_ids: list[str]) -> None:
        self.members_added = inbox_ids

    async def remove_members_by_inbox_id(self, inbox_ids: list[str]) -> None:
        self.members_removed = inbox_ids

    async def add_members(self, identifiers: list[Any]) -> None:
        self.added_identifiers = identifiers

    async def remove_members(self, identifiers: list[Any]) -> None:
        self.removed_identifiers = identifiers

    async def list_members(self) -> list[_Member]:
        return [_Member(inbox_id='one'), _Member(inbox_id='two')]

    async def add_admin(self, inbox_id: str) -> None:
        self.admin_added = inbox_id

    async def remove_admin(self, inbox_id: str) -> None:
        self.admin_removed = inbox_id

    async def is_admin(self, inbox_id: str) -> bool:
        return inbox_id == 'admin'

    async def is_super_admin(self, inbox_id: str) -> bool:
        return inbox_id == 'super'

    def group_name(self) -> str:
        return 'group-name'

    def group_description(self) -> str:
        return 'group-description'

    def group_image_url_square(self) -> str:
        return 'https://image'


class _RaisingConversation(_FakeFfiConversation):
    def consent_state(self) -> str:
        raise RuntimeError('no consent')

    def group_name(self) -> str:
        raise RuntimeError('no name')

    def group_description(self) -> str:
        raise RuntimeError('no description')

    def group_image_url_square(self) -> str:
        raise RuntimeError('no image')


class _SyncConsentConversation(_FakeFfiConversation):
    def update_consent_state(self, state: Any) -> None:
        self._consent_state = state


class _SyncAdminConversation(_FakeFfiConversation):
    def is_admin(self, inbox_id: str) -> bool:
        return inbox_id == 'admin'

    def is_super_admin(self, inbox_id: str) -> bool:
        return inbox_id == 'super'


class _FakeClient:
    def __init__(self) -> None:
        self.encoded: tuple[Any, Any] | None = None

    def encode_content(self, content: Any, content_type: Any) -> bytes:
        self.encoded = (content, content_type)
        return b'encoded'


@pytest.mark.asyncio
async def test_conversation_send_text() -> None:
    ffi = _FakeFfiConversation()
    convo = Conversation(_FakeClient(), ffi)
    result = await convo.send('hello')
    assert result == b'msg-id'
    assert ffi.sent_text == 'hello'
    assert convo.id == b'cid'
    assert convo.consent_state == 'allowed'
    await convo.update_consent_state('denied')
    assert ffi._consent_state == 'denied'


@pytest.mark.asyncio
async def test_conversation_update_consent_state_sync() -> None:
    ffi = _SyncConsentConversation()
    convo = Conversation(_FakeClient(), ffi)
    await convo.update_consent_state('denied')
    assert ffi._consent_state == 'denied'


@pytest.mark.asyncio
async def test_conversation_send_requires_content_type() -> None:
    ffi = _FakeFfiConversation()
    convo = Conversation(_FakeClient(), ffi)
    with pytest.raises(MissingContentTypeError):
        await convo.send(b'data')


def test_default_send_opts_fallback(monkeypatch) -> None:
    import xmtp.conversation as conversation

    class _Bindings:
        pass

    monkeypatch.setattr(conversation, 'NativeBindings', _Bindings(), raising=False)
    opts = conversation._default_send_opts()
    assert opts.should_push is True


@pytest.mark.asyncio
async def test_conversation_send_encoded() -> None:
    ffi = _FakeFfiConversation()
    client = _FakeClient()
    convo = Conversation(client, ffi)
    result = await convo.send({'x': 1}, 'custom')
    assert result == b'msg-id'
    assert client.encoded == ({'x': 1}, 'custom')
    assert ffi.sent_payload == b'encoded'
    assert ffi.sent_opts.should_push is True


def test_consent_state_optional() -> None:
    convo = Conversation(_FakeClient(), _RaisingConversation())
    assert convo.consent_state is None


def test_dm_peer_inbox_id() -> None:
    dm = Dm(_FakeClient(), _FakeFfiConversation())
    assert dm.peer_inbox_id == 'peer'


@pytest.mark.asyncio
async def test_group_members_and_admins(fake_bindings) -> None:
    group = Group(_FakeClient(), _FakeFfiConversation())
    await group.add_members(['one'])
    await group.remove_members(['two'])
    await group.add_members_by_identifiers([
        Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc')
    ])
    await group.remove_members_by_identifiers([
        Identifier(kind=IdentifierKind.PASSKEY, value='pass')
    ])
    assert group._ffi.members_added == ['one']
    assert group._ffi.members_removed == ['two']

    members = await group.members()
    assert members == ['one', 'two']

    await group.add_admin('admin')
    await group.remove_admin('admin')
    assert await group.is_admin('admin') is True
    assert await group.is_super_admin('super') is True
    assert group.name == 'group-name'
    assert group.description == 'group-description'
    assert group.image_url == 'https://image'


@pytest.mark.asyncio
async def test_group_admin_checks_sync() -> None:
    group = Group(_FakeClient(), _SyncAdminConversation())
    assert await group.is_admin('admin') is True
    assert await group.is_super_admin('super') is True


def test_group_optional_fields() -> None:
    group = Group(_FakeClient(), _RaisingConversation())
    assert group.name is None
    assert group.description is None
    assert group.image_url is None
