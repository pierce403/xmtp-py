"""User preferences management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xmtp.bindings import NativeBindings
from xmtp.errors import ClientNotInitializedError

if TYPE_CHECKING:
    from xmtp.client import Client
    from xmtp.conversations import Conversations


class Preferences:
    """Manage user preferences for the XMTP client."""

    def __init__(self, client: Client, conversations: Conversations) -> None:
        self._client = client
        self._conversations = conversations

    def _ensure(self) -> NativeBindings.FfiXmtpClient:
        if self._client._client is None:
            raise ClientNotInitializedError()
        return self._client._client

    async def refresh(self) -> None:
        """Refresh preferences from the network."""

        await self._ensure().sync_preferences()

    async def inbox_state(self, refresh_from_network: bool = False) -> NativeBindings.FfiInboxState:
        """Return the current inbox state."""

        return await self._ensure().inbox_state(refresh_from_network)

    async def get_latest_inbox_state(self, inbox_id: str) -> NativeBindings.FfiInboxState:
        """Return the latest inbox state for a specific inbox."""

        return await self._ensure().get_latest_inbox_state(inbox_id)

    async def inbox_state_from_inbox_ids(
        self, inbox_ids: list[str], refresh_from_network: bool = False
    ) -> list[NativeBindings.FfiInboxState]:
        """Return inbox state for the specified inbox IDs."""

        return await self._ensure().addresses_from_inbox_id(refresh_from_network, inbox_ids)

    async def set_consent_states(self, records: list[NativeBindings.FfiConsent]) -> None:
        """Update consent states for multiple records."""

        await self._ensure().set_consent_states(records)

    async def get_consent_state(
        self, entity_type: NativeBindings.FfiConsentEntityType, entity: str
    ) -> NativeBindings.FfiConsentState:
        """Get consent state for a specific entity."""

        return await self._ensure().get_consent_state(entity_type, entity)
