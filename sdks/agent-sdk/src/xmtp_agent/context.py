"""Context objects for agent handlers."""

from __future__ import annotations

from xmtp import Client, Conversation, DecodedMessage, Dm, Group
from xmtp.bindings import NativeBindings
from xmtp_content_type_markdown import ContentTypeMarkdown
from xmtp_content_type_primitives import ContentCodec, ContentTypeId
from xmtp_content_type_reaction import (
    ContentTypeReaction,
    Reaction,
    ReactionAction,
    ReactionSchema,
)
from xmtp_content_type_remote_attachment import ContentTypeRemoteAttachment, RemoteAttachment
from xmtp_content_type_reply import ContentTypeReply, Reply
from xmtp_content_type_text import ContentTypeText


class ClientContext:
    """Context passed to lifecycle handlers."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @property
    def client(self) -> Client:
        return self._client

    def get_client_address(self) -> str | None:
        identifier = self._client.account_identifier
        return identifier.value if identifier else None


class ConversationContext(ClientContext):
    """Context passed to conversation handlers."""

    def __init__(self, conversation: Conversation, client: Client) -> None:
        super().__init__(client)
        self._conversation = conversation

    def is_dm(self) -> bool:
        return isinstance(self._conversation, Dm)

    def is_group(self) -> bool:
        return isinstance(self._conversation, Group)

    async def send_markdown(self, markdown: str) -> None:
        await self._conversation.send(markdown, ContentTypeMarkdown)

    async def send_text(self, text: str) -> None:
        await self._conversation.send(text)

    async def send_remote_attachment(self, attachment: RemoteAttachment) -> None:
        await self._conversation.send(attachment, ContentTypeRemoteAttachment)

    @property
    def conversation(self) -> Conversation:
        return self._conversation

    @property
    def is_allowed(self) -> bool:
        return self._conversation.consent_state == NativeBindings.FfiConsentState.ALLOWED

    @property
    def is_denied(self) -> bool:
        return self._conversation.consent_state == NativeBindings.FfiConsentState.DENIED

    @property
    def is_unknown(self) -> bool:
        return self._conversation.consent_state == NativeBindings.FfiConsentState.UNKNOWN


class MessageContext(ConversationContext):
    """Context passed to message handlers."""

    def __init__(
        self,
        message: DecodedMessage[object],
        conversation: Conversation,
        client: Client,
    ) -> None:
        super().__init__(conversation=conversation, client=client)
        self._message = message

    def uses_codec(self, codec_class: type[ContentCodec[object]]) -> bool:
        return self._message.content_type_id == str(codec_class().content_type)

    def is_markdown(self) -> bool:
        return self._message.content_type_id == str(ContentTypeMarkdown)

    def is_text(self) -> bool:
        return self._message.content_type_id == str(ContentTypeText)

    def is_reply(self) -> bool:
        return self._message.content_type_id == str(ContentTypeReply)

    def is_reaction(self) -> bool:
        return self._message.content_type_id == str(ContentTypeReaction)

    def is_remote_attachment(self) -> bool:
        return self._message.content_type_id == str(ContentTypeRemoteAttachment)

    async def send_reaction(
        self,
        content: str,
        schema: ReactionSchema = ReactionSchema.UNICODE,
    ) -> None:
        reaction = Reaction(
            action=ReactionAction.ADDED,
            reference=self._message.id.hex(),
            reference_inbox_id=self._message.sender_inbox_id,
            schema=schema,
            content=content,
        )
        await self._conversation.send(reaction, ContentTypeReaction)

    async def _send_reply(self, text: str, content_type: ContentTypeId) -> None:
        reply = Reply(
            reference=self._message.id.hex(),
            reference_inbox_id=self._message.sender_inbox_id,
            content_type=content_type,
            content=text,
        )
        await self._conversation.send(reply, ContentTypeReply)

    async def send_text_reply(self, text: str) -> None:
        await self._send_reply(text, ContentTypeText)

    async def send_markdown_reply(self, markdown: str) -> None:
        await self._send_reply(markdown, ContentTypeMarkdown)

    async def get_sender_address(self) -> str | None:
        states = await self.client.preferences.inbox_state_from_inbox_ids(
            [self._message.sender_inbox_id],
            refresh_from_network=False,
        )
        if not states:
            return None
        identifiers = states[0].account_identities
        if not identifiers:
            return None
        return identifiers[0].identifier

    @property
    def message(self) -> DecodedMessage[object]:
        return self._message
