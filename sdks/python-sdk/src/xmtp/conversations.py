"""Conversation management."""

from __future__ import annotations

import asyncio
import builtins
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from xmtp.async_stream import AsyncStream
from xmtp.bindings import NativeBindings
from xmtp.conversation import Conversation, Dm, Group
from xmtp.errors import ClientNotInitializedError
from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.messages import DecodedMessage

if TYPE_CHECKING:
    from xmtp.client import Client


@dataclass(slots=True)
class ListConversationsOptions:
    """Options for listing conversations."""

    created_after_ns: int | None = None
    created_before_ns: int | None = None
    last_activity_before_ns: int | None = None
    last_activity_after_ns: int | None = None
    order_by: NativeBindings.FfiGroupQueryOrderBy | None = None
    limit: int | None = None
    consent_states: list[NativeBindings.FfiConsentState] | None = None
    include_duplicate_dms: bool = False

    def to_ffi(self) -> NativeBindings.FfiListConversationsOptions:
        return NativeBindings.FfiListConversationsOptions(
            created_after_ns=self.created_after_ns,
            created_before_ns=self.created_before_ns,
            last_activity_before_ns=self.last_activity_before_ns,
            last_activity_after_ns=self.last_activity_after_ns,
            order_by=self.order_by,
            limit=self.limit,
            consent_states=self.consent_states,
            include_duplicate_dms=self.include_duplicate_dms,
        )


def _identifier_to_ffi(identifier: Identifier) -> NativeBindings.FfiIdentifier:
    kind = {
        IdentifierKind.ETHEREUM: NativeBindings.FfiIdentifierKind.ETHEREUM,
        IdentifierKind.PASSKEY: NativeBindings.FfiIdentifierKind.PASSKEY,
    }[identifier.kind]
    return NativeBindings.FfiIdentifier(identifier=identifier.value, identifier_kind=kind)


def _default_dm_options() -> NativeBindings.FfiCreateDmOptions:
    return NativeBindings.FfiCreateDmOptions(message_disappearing_settings=None)


def _default_group_options() -> NativeBindings.FfiCreateGroupOptions:
    return NativeBindings.FfiCreateGroupOptions(
        permissions=None,
        group_name=None,
        group_image_url_square=None,
        group_description=None,
        custom_permission_policy_set=None,
        message_disappearing_settings=None,
        app_data=None,
    )


def _default_list_options() -> NativeBindings.FfiListConversationsOptions:
    return ListConversationsOptions().to_ffi()


class Conversations:
    """Manage XMTP conversations."""

    def __init__(
        self,
        client: Client,
        ffi_conversations: NativeBindings.FfiConversations | None,
    ) -> None:
        self._client = client
        self._ffi = ffi_conversations

    def _ensure(self) -> NativeBindings.FfiConversations:
        if self._ffi is None:
            raise ClientNotInitializedError()
        return self._ffi

    async def new_dm(self, address: str) -> Dm:
        """Create a new direct message conversation by address."""

        identifier = Identifier(kind=IdentifierKind.ETHEREUM, value=address)
        return await self.new_dm_with_identifier(identifier)

    async def new_dm_with_identifier(self, identifier: Identifier) -> Dm:
        """Create a new direct message using an identifier."""

        inbox_id = await self._client.get_inbox_id_by_identifier(identifier)
        if inbox_id is None:
            raise ValueError(f'No inbox id found for identifier "{identifier.value}"')

        ffi = self._ensure()
        options = _default_dm_options()

        if hasattr(ffi, "find_or_create_dm_by_inbox_id"):
            try:
                group = await ffi.find_or_create_dm_by_inbox_id(inbox_id, options)
                return Dm(self._client, group)
            except TypeError:
                pass

        try:
            group = await ffi.find_or_create_dm(_identifier_to_ffi(identifier), options)
        except TypeError:
            group = await ffi.find_or_create_dm(inbox_id, options)
        return Dm(self._client, group)

    async def new_group(self, members: list[str]) -> Group:
        """Create a new group conversation by member addresses."""

        identifiers = [Identifier(kind=IdentifierKind.ETHEREUM, value=member) for member in members]
        return await self.new_group_with_identifiers(identifiers)

    async def new_group_with_identifiers(self, identifiers: list[Identifier]) -> Group:
        """Create a new group conversation using identifiers."""

        group = await self._ensure().create_group(
            [_identifier_to_ffi(identifier) for identifier in identifiers],
            _default_group_options(),
        )
        return Group(self._client, group)

    async def list(
        self,
        options: ListConversationsOptions | None = None,
    ) -> builtins.list[Conversation]:
        """List all conversations."""

        items = self._ensure().list((options or ListConversationsOptions()).to_ffi())
        return [self._wrap_conversation(item.conversation()) for item in items]

    async def list_dms(
        self,
        options: ListConversationsOptions | None = None,
    ) -> builtins.list[Dm]:
        """List direct message conversations."""

        items = self._ensure().list_dms((options or ListConversationsOptions()).to_ffi())
        return [Dm(self._client, item.conversation()) for item in items]

    async def list_groups(
        self,
        options: ListConversationsOptions | None = None,
    ) -> builtins.list[Group]:
        """List group conversations."""

        items = self._ensure().list_groups((options or ListConversationsOptions()).to_ffi())
        return [Group(self._client, item.conversation()) for item in items]

    async def get_conversation_by_id(self, conversation_id: bytes) -> Conversation | None:
        """Return a conversation by identifier."""

        try:
            if self._client._client is None:
                raise ClientNotInitializedError()
            convo = self._client._client.conversation(conversation_id)
        except Exception:
            return None
        return self._wrap_conversation(convo)

    def stream(self) -> AsyncStream[Conversation | NativeBindings.FfiSubscribeError]:
        """Stream new conversations."""

        queue: asyncio.Queue[object] = asyncio.Queue()
        loop = asyncio.get_event_loop()

        class Callback(NativeBindings.FfiConversationCallback):
            def on_conversation(
                self,
                conversation: NativeBindings.FfiConversation,
            ) -> None:
                conv = self_outer._wrap_conversation(conversation)
                loop.call_soon_threadsafe(queue.put_nowait, conv)

            def on_error(
                self,
                error: NativeBindings.FfiSubscribeError,
            ) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, error)

            def on_close(self) -> None:
                loop.call_soon_threadsafe(stream._end)

        self_outer = self
        callback = Callback()
        stream: AsyncStream[Conversation | NativeBindings.FfiSubscribeError] = AsyncStream(queue)

        async def start() -> None:
            closer = await self._ensure().stream(callback)

            async def close() -> None:
                await closer.end_and_wait()

            stream._closer = close

        asyncio.create_task(start())
        return stream

    def stream_all_messages(
        self,
    ) -> AsyncStream[DecodedMessage[object] | NativeBindings.FfiSubscribeError]:
        """Stream all messages across conversations."""

        queue: asyncio.Queue[object] = asyncio.Queue()
        loop = asyncio.get_event_loop()
        client = self._client

        class Callback(NativeBindings.FfiMessageCallback):
            def on_message(
                self,
                message: NativeBindings.FfiMessage,
            ) -> None:
                decoded = client._decode_message(message)
                loop.call_soon_threadsafe(queue.put_nowait, decoded)

            def on_error(
                self,
                error: NativeBindings.FfiSubscribeError,
            ) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, error)

            def on_close(self) -> None:
                loop.call_soon_threadsafe(stream._end)

        callback = Callback()
        stream: AsyncStream[DecodedMessage[object] | NativeBindings.FfiSubscribeError] = (
            AsyncStream(queue)
        )

        async def start() -> None:
            closer = await self._ensure().stream_all_messages(callback, None)

            async def close() -> None:
                await closer.end_and_wait()

            stream._closer = close

        asyncio.create_task(start())
        return stream

    async def sync(self) -> None:
        """Sync new conversations."""

        await self._ensure().sync()

    async def sync_all_conversations(
        self,
        consent_states: builtins.list[NativeBindings.FfiConsentState] | None = None,
    ) -> None:
        """Sync all conversations."""
        ffi = self._ensure()
        if consent_states is None:
            try:
                signature = inspect.signature(ffi.sync_all_conversations)
            except (TypeError, ValueError):
                await ffi.sync_all_conversations(consent_states)
                return
            if len(signature.parameters) == 0:
                await cast(Any, ffi).sync_all_conversations()
                return
        await ffi.sync_all_conversations(consent_states)

    def _wrap_conversation(self, convo: NativeBindings.FfiConversation) -> Conversation:
        convo_type = convo.conversation_type()
        if convo_type == NativeBindings.FfiConversationType.DM:
            return Dm(self._client, convo)
        return Group(self._client, convo)
