from __future__ import annotations

from dataclasses import dataclass

import pytest

from xmtp.errors import ClientNotInitializedError
from xmtp.preferences import Preferences


@dataclass
class _FakeClient:
    _client: object | None


class _FfiClient:
    async def sync_preferences(self) -> None:
        self.synced = True

    async def inbox_state(self, refresh_from_network: bool) -> dict[str, bool]:
        return {'refresh': refresh_from_network}

    async def get_latest_inbox_state(self, inbox_id: str) -> dict[str, str]:
        return {'inbox_id': inbox_id}

    async def addresses_from_inbox_id(self, refresh_from_network: bool, inbox_ids: list[str]):
        return [{'inbox_id': inbox_id} for inbox_id in inbox_ids]

    async def set_consent_states(self, records):
        self.consent_records = records

    async def get_consent_state(self, entity_type, entity):
        return {'entity_type': entity_type, 'entity': entity}


@pytest.mark.asyncio
async def test_preferences_requires_client() -> None:
    prefs = Preferences(_FakeClient(None), object())
    with pytest.raises(ClientNotInitializedError):
        await prefs.refresh()


@pytest.mark.asyncio
async def test_preferences_methods() -> None:
    ffi_client = _FfiClient()
    prefs = Preferences(_FakeClient(ffi_client), object())
    await prefs.refresh()
    assert await prefs.inbox_state() == {'refresh': False}
    assert await prefs.inbox_state(True) == {'refresh': True}
    assert await prefs.get_latest_inbox_state('inbox') == {'inbox_id': 'inbox'}
    assert await prefs.inbox_state_from_inbox_ids(['a', 'b']) == [
        {'inbox_id': 'a'},
        {'inbox_id': 'b'},
    ]
    await prefs.set_consent_states(['record'])
    assert await prefs.get_consent_state('type', 'entity') == {
        'entity_type': 'type',
        'entity': 'entity',
    }
