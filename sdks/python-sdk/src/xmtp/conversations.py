"""Conversation management."""

from __future__ import annotations

import builtins

from xmtp.async_stream import AsyncStream
from xmtp.conversation import Conversation, Dm, Group
from xmtp.errors import NotImplementedXmtpError


class Conversations:
    """Manage XMTP conversations."""

    async def new_dm(self, address: str) -> Dm:
        """Create a new direct message conversation by address."""

        raise NotImplementedXmtpError('Conversations.new_dm not implemented')

    async def new_dm_with_identifier(self, identifier: str) -> Dm:
        """Create a new direct message using an identifier."""

        raise NotImplementedXmtpError(
            'Conversations.new_dm_with_identifier not implemented'
        )

    async def new_group(self, members: list[str]) -> Group:
        """Create a new group conversation by member addresses."""

        raise NotImplementedXmtpError('Conversations.new_group not implemented')

    async def new_group_with_identifiers(self, identifiers: list[str]) -> Group:
        """Create a new group conversation using identifiers."""

        raise NotImplementedXmtpError(
            'Conversations.new_group_with_identifiers not implemented'
        )

    async def list(self) -> builtins.list[Conversation]:
        """List all conversations."""

        raise NotImplementedXmtpError('Conversations.list not implemented')

    async def list_dms(self) -> builtins.list[Dm]:
        """List direct message conversations."""

        raise NotImplementedXmtpError('Conversations.list_dms not implemented')

    async def list_groups(self) -> builtins.list[Group]:
        """List group conversations."""

        raise NotImplementedXmtpError('Conversations.list_groups not implemented')

    async def get_conversation_by_id(self, conversation_id: str) -> Conversation | None:
        """Return a conversation by identifier."""

        raise NotImplementedXmtpError(
            'Conversations.get_conversation_by_id not implemented'
        )

    def stream(self) -> AsyncStream[Conversation]:
        """Stream new conversations."""

        raise NotImplementedXmtpError('Conversations.stream not implemented')

    def stream_all_messages(self) -> AsyncStream[Conversation]:
        """Stream all messages across conversations."""

        raise NotImplementedXmtpError('Conversations.stream_all_messages not implemented')

    async def sync(self) -> None:
        """Sync new conversations."""

        raise NotImplementedXmtpError('Conversations.sync not implemented')

    async def sync_all_conversations(self) -> None:
        """Sync all conversations."""

        raise NotImplementedXmtpError('Conversations.sync_all_conversations not implemented')
