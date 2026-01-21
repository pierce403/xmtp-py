import pytest
from dataclasses import dataclass
from enum import Enum

from xmtp.identifiers import Identifier, IdentifierKind
from xmtp_agent.recipient_resolver import ResolvedRecipient, resolve_recipient


class _Identity:
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier


class _InboxState:
    def __init__(self, address: str | None) -> None:
        self.recovery_identity = _Identity(address or '')
        self.account_identities = []


class _InboxStateNoRecovery:
    def __init__(self, address: str) -> None:
        self.recovery_identity = None
        self.account_identities = [_Identity(address)]


class _Preferences:
    def __init__(self, inbox_state: object | None = None) -> None:
        self._inbox_state = inbox_state
        self.consent_records = None

    async def get_latest_inbox_state(self, inbox_id: str):
        return self._inbox_state

    async def set_consent_states(self, records):
        self.consent_records = records


class _Client:
    def __init__(self, inbox_map=None, inbox_state=None) -> None:
        self._inbox_map = inbox_map or {}
        self.preferences = _Preferences(inbox_state)

    async def get_inbox_id_by_identifier(self, identifier: Identifier):
        return self._inbox_map.get(identifier.value)


class _FailingPreferences(_Preferences):
    async def get_latest_inbox_state(self, inbox_id: str):
        raise RuntimeError('fail')


@pytest.mark.asyncio
async def test_resolve_recipient_inbox_id() -> None:
    inbox_id = '1' * 64
    address = '0x' + 'a' * 40
    client = _Client(inbox_state=_InboxState(address))

    resolved = await resolve_recipient(client, inbox_id)
    assert isinstance(resolved, ResolvedRecipient)
    assert resolved.inbox_id == inbox_id
    assert resolved.address == address
    assert resolved.identifier == Identifier(kind=IdentifierKind.ETHEREUM, value=address)


@pytest.mark.asyncio
async def test_resolve_recipient_inbox_id_without_state() -> None:
    inbox_id = '7' * 64
    client = _Client(inbox_state=None)
    client.preferences = _FailingPreferences()

    resolved = await resolve_recipient(client, inbox_id)
    assert resolved.inbox_id == inbox_id
    assert resolved.address is None


@pytest.mark.asyncio
async def test_resolve_recipient_inbox_id_no_address() -> None:
    inbox_id = '8' * 64
    client = _Client(inbox_state=_InboxState('not-hex'))

    resolved = await resolve_recipient(client, inbox_id)
    assert resolved.inbox_id == inbox_id
    assert resolved.address is None


@pytest.mark.asyncio
async def test_resolve_recipient_inbox_id_no_recovery_identity() -> None:
    inbox_id = '9' * 64
    address = '0x' + 'a' * 40
    client = _Client(inbox_state=_InboxStateNoRecovery(address))

    resolved = await resolve_recipient(client, inbox_id)
    assert resolved.inbox_id == inbox_id
    assert resolved.address == address

@pytest.mark.asyncio
async def test_resolve_recipient_address() -> None:
    address = '0x' + 'b' * 40
    inbox_id = '2' * 64
    client = _Client(inbox_map={address: inbox_id})

    resolved = await resolve_recipient(client, address)
    assert resolved.inbox_id == inbox_id
    assert resolved.address == address


@pytest.mark.asyncio
async def test_resolve_recipient_identifier() -> None:
    address = '0x' + 'f' * 40
    inbox_id = '5' * 64
    client = _Client(inbox_map={address: inbox_id})

    identifier = Identifier(kind=IdentifierKind.ETHEREUM, value=address)
    resolved = await resolve_recipient(client, identifier)
    assert resolved.inbox_id == inbox_id
    assert resolved.address == address
    assert resolved.identifier == Identifier(kind=IdentifierKind.ETHEREUM, value=address)


@pytest.mark.asyncio
async def test_resolve_recipient_identifier_missing_inbox_id() -> None:
    address = '0x' + 'f' * 40
    client = _Client(inbox_map={})
    identifier = Identifier(kind=IdentifierKind.ETHEREUM, value=address)

    with pytest.raises(ValueError, match='No inbox id found'):
        await resolve_recipient(client, identifier)


@pytest.mark.asyncio
async def test_resolve_recipient_identifier_invalid_address() -> None:
    client = _Client(inbox_map={})
    identifier = Identifier(kind=IdentifierKind.ETHEREUM, value='not-hex')

    with pytest.raises(ValueError, match='Invalid address'):
        await resolve_recipient(client, identifier)


@pytest.mark.asyncio
async def test_resolve_recipient_identifier_non_eth() -> None:
    inbox_id = '6' * 64
    client = _Client(inbox_map={'passkey': inbox_id})

    identifier = Identifier(kind=IdentifierKind.PASSKEY, value='passkey')
    resolved = await resolve_recipient(client, identifier)
    assert resolved.inbox_id == inbox_id
    assert resolved.address is None


@pytest.mark.asyncio
async def test_resolve_recipient_name() -> None:
    address = '0x' + 'c' * 40
    inbox_id = '3' * 64
    client = _Client(inbox_map={address: inbox_id})

    async def fake_resolver(name: str):
        return address

    resolved = await resolve_recipient(client, 'vitalik.eth', name_resolver=fake_resolver)
    assert resolved.inbox_id == inbox_id
    assert resolved.address == address


@pytest.mark.asyncio
async def test_resolve_recipient_name_unresolved() -> None:
    client = _Client()

    async def fake_resolver(name: str):
        return None

    with pytest.raises(ValueError, match='Could not resolve address'):
        await resolve_recipient(client, 'vitalik.eth', name_resolver=fake_resolver)


@pytest.mark.asyncio
async def test_resolve_recipient_requires_name_resolver() -> None:
    client = _Client()
    with pytest.raises(ValueError, match='Name resolver required'):
        await resolve_recipient(client, 'vitalik.eth')


@pytest.mark.asyncio
async def test_resolve_recipient_missing_inbox_id() -> None:
    address = '0x' + 'd' * 40
    client = _Client(inbox_map={})
    with pytest.raises(ValueError, match='No inbox id found'):
        await resolve_recipient(client, address)


@pytest.mark.asyncio
async def test_resolve_recipient_sets_consent(monkeypatch) -> None:
    class _ConsentEntityType(str, Enum):
        INBOX_ID = 'inbox_id'

    @dataclass
    class _Consent:
        entity_type: _ConsentEntityType
        state: object
        entity: str

    class _Bindings:
        FfiConsentEntityType = _ConsentEntityType
        FfiConsent = _Consent

    monkeypatch.setattr('xmtp_agent.recipient_resolver.NativeBindings', _Bindings, raising=False)

    address = '0x' + 'e' * 40
    inbox_id = '4' * 64
    client = _Client(inbox_map={address: inbox_id})
    state = object()

    resolved = await resolve_recipient(client, address, consent_state=state)
    assert resolved.inbox_id == inbox_id
    records = client.preferences.consent_records
    assert records is not None
    assert records[0].entity == inbox_id
    assert records[0].entity_type == _ConsentEntityType.INBOX_ID
    assert records[0].state is state
