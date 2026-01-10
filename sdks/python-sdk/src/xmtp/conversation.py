"""Conversation models."""

from __future__ import annotations

from typing import Any

from xmtp.bindings import NativeBindings
from xmtp.errors import MissingContentTypeError
from xmtp.identifiers import Identifier, IdentifierKind


def _identifier_to_ffi(identifier: Identifier) -> NativeBindings.FfiIdentifier:
    kind = {
        IdentifierKind.ETHEREUM: NativeBindings.FfiIdentifierKind.ETHEREUM,
        IdentifierKind.PASSKEY: NativeBindings.FfiIdentifierKind.PASSKEY,
    }[identifier.kind]
    return NativeBindings.FfiIdentifier(identifier=identifier.value, identifier_kind=kind)


class Conversation:
    """Base conversation class."""

    def __init__(self, client: Any, ffi_conversation: NativeBindings.FfiConversation) -> None:
        self._client = client
        self._ffi = ffi_conversation

    @property
    def id(self) -> bytes:
        """Conversation identifier bytes."""

        return self._ffi.id()

    @property
    def consent_state(self) -> NativeBindings.FfiConsentState | None:
        """Return the conversation consent state if available."""

        try:
            return self._ffi.consent_state()
        except Exception:
            return None

    async def update_consent_state(self, state: NativeBindings.FfiConsentState) -> None:
        """Update the conversation consent state."""

        await self._ffi.update_consent_state(state)

    async def send(
        self,
        content: str | bytes | Any,
        content_type: Any | None = None,
    ) -> bytes:
        """Send a message in the conversation."""

        if isinstance(content, str) and content_type is None:
            return await self._ffi.send_text(content)

        if content_type is None:
            raise MissingContentTypeError()

        encoded = self._client.encode_content(content, content_type)
        opts = NativeBindings.FfiSendMessageOpts(should_push=True)
        return await self._ffi.send(encoded, opts)


class Dm(Conversation):
    """Direct message conversation."""

    @property
    def peer_inbox_id(self) -> str | None:
        """Inbox ID of the DM peer, if available."""

        return self._ffi.dm_peer_inbox_id()


class Group(Conversation):
    """Group conversation."""

    async def add_members(self, inbox_ids: list[str]) -> None:
        """Add members to the group by inbox ID."""

        await self._ffi.add_members_by_inbox_id(inbox_ids)

    async def remove_members(self, inbox_ids: list[str]) -> None:
        """Remove members from the group by inbox ID."""

        await self._ffi.remove_members_by_inbox_id(inbox_ids)

    async def add_members_by_identifiers(self, identifiers: list[Identifier]) -> None:
        """Add members to the group by identifier."""

        await self._ffi.add_members([_identifier_to_ffi(identifier) for identifier in identifiers])

    async def remove_members_by_identifiers(self, identifiers: list[Identifier]) -> None:
        """Remove members from the group by identifier."""

        await self._ffi.remove_members([_identifier_to_ffi(identifier) for identifier in identifiers])

    async def members(self) -> list[str]:
        """Return group member inbox IDs."""

        members = await self._ffi.list_members()
        return [member.inbox_id for member in members]

    async def add_admin(self, inbox_id: str) -> None:
        """Add an admin to the group."""

        await self._ffi.add_admin(inbox_id)

    async def remove_admin(self, inbox_id: str) -> None:
        """Remove an admin from the group."""

        await self._ffi.remove_admin(inbox_id)

    async def is_admin(self, inbox_id: str) -> bool:
        """Return True if inbox_id is an admin."""

        return await self._ffi.is_admin(inbox_id)

    async def is_super_admin(self, inbox_id: str) -> bool:
        """Return True if inbox_id is a super admin."""

        return await self._ffi.is_super_admin(inbox_id)

    @property
    def name(self) -> str | None:
        """Group name."""

        try:
            return self._ffi.group_name()
        except Exception:
            return None

    @property
    def description(self) -> str | None:
        """Group description."""

        try:
            return self._ffi.group_description()
        except Exception:
            return None

    @property
    def image_url(self) -> str | None:
        """Group image URL."""

        try:
            return self._ffi.group_image_url_square()
        except Exception:
            return None
