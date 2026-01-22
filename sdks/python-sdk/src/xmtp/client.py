"""XMTP client entry point."""

from __future__ import annotations

import inspect
import os
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, TypeVar, cast

from xmtp_content_type_primitives import ContentCodec, ContentTypeId, EncodedContent

from xmtp.bindings import NativeBindings
from xmtp.conversations import Conversations
from xmtp.env import (
    apply_rust_log_from_options,
    load_client_options_from_env,
    load_signer_from_env,
)
from xmtp.errors import (
    ClientNotInitializedError,
    CodecNotFoundError,
    DatabaseOpenError,
    SignerUnavailableError,
)
from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.messages import DecodedMessage
from xmtp.preferences import Preferences
from xmtp.signers.base import Signer, SignerType
from xmtp.types import ClientOptions
from xmtp.utils import coerce_db_encryption_key

ContentT = TypeVar("ContentT")

_DB_ERROR_MARKERS = (
    "sqlcipher",
    "sqlite",
    "database",
    "db3",
    "file is encrypted",
    "not a database",
    "cipher",
    "malformed",
)


def _identifier_to_ffi(identifier: Identifier) -> NativeBindings.FfiIdentifier:
    kind = {
        IdentifierKind.ETHEREUM: NativeBindings.FfiIdentifierKind.ETHEREUM,
        IdentifierKind.PASSKEY: NativeBindings.FfiIdentifierKind.PASSKEY,
    }[identifier.kind]
    return NativeBindings.FfiIdentifier(identifier=identifier.value, identifier_kind=kind)


@dataclass(slots=True)
class _SendMessageOpts:
    should_push: bool


def _default_send_opts(
    should_push: bool = True,
) -> NativeBindings.FfiSendMessageOpts | _SendMessageOpts:
    try:
        return NativeBindings.FfiSendMessageOpts(should_push=should_push)
    except Exception:
        return _SendMessageOpts(should_push=should_push)


def _content_type_from_ffi(
    content_type: NativeBindings.FfiContentTypeId | None,
) -> ContentTypeId | None:
    if content_type is None:
        return None
    return ContentTypeId(
        authority_id=content_type.authority_id,
        type_id=content_type.type_id,
        version_major=content_type.version_major,
        version_minor=content_type.version_minor,
    )


def _encoded_from_ffi(encoded: NativeBindings.FfiEncodedContent) -> EncodedContent:
    content_type = _content_type_from_ffi(encoded.type_id)
    if content_type is None:
        raise ValueError("Missing content type in encoded content")
    return EncodedContent(
        type_id=content_type,
        parameters=encoded.parameters,
        fallback=encoded.fallback,
        compression=encoded.compression,
        content=encoded.content,
    )


def _looks_like_db_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in _DB_ERROR_MARKERS)


class Client:
    """Main client for interacting with the XMTP network."""

    def __init__(self, options: ClientOptions | None = None) -> None:
        self._options = options or ClientOptions()
        self._signer: Signer | None = None
        self._identifier: Identifier | None = None
        self._client: NativeBindings.FfiXmtpClient | None = None
        self._conversations: Conversations | None = None
        self._preferences: Preferences | None = None
        self._codecs: dict[str, ContentCodec[object]] = {}
        self._register_default_codecs()
        if self._options.codecs:
            for codec in self._options.codecs:
                self.register_codec(codec)

    def _register_default_codecs(self) -> None:
        try:
            import xmtp_bindings  # noqa: F401
        except ImportError:
            return

        try:
            from xmtp_content_type_group_updated import GroupUpdatedCodec
            from xmtp_content_type_markdown import MarkdownCodec
            from xmtp_content_type_reaction import ReactionCodec
            from xmtp_content_type_read_receipt import ReadReceiptCodec
            from xmtp_content_type_remote_attachment import AttachmentCodec, RemoteAttachmentCodec
            from xmtp_content_type_reply import ReplyCodec
            from xmtp_content_type_text import TextCodec
            from xmtp_content_type_transaction_reference import TransactionReferenceCodec
            from xmtp_content_type_wallet_send_calls import WalletSendCallsCodec
        except ImportError:
            return

        for codec in (
            TextCodec(),
            MarkdownCodec(),
            ReactionCodec(),
            ReadReceiptCodec(),
            AttachmentCodec(),
            RemoteAttachmentCodec(),
            ReplyCodec(),
            GroupUpdatedCodec(),
            TransactionReferenceCodec(),
            WalletSendCallsCodec(),
        ):
            self.register_codec(cast(ContentCodec[object], codec))

    @classmethod
    async def create(cls, signer: Signer, options: ClientOptions | None = None) -> Client:
        """Create a client with a signer."""

        client = cls(options)
        client._signer = signer
        identifier = await signer.get_identifier()
        await client._init(identifier)
        if not client._options.disable_auto_register:
            await client.register()
        return client

    @classmethod
    async def create_from_env(cls, options: ClientOptions | None = None) -> Client:
        """Create a client using XMTP environment variables."""

        signer = load_signer_from_env()
        opts = load_client_options_from_env(options)
        return await cls.create(signer, opts)

    @classmethod
    async def from_env(cls, options: ClientOptions | None = None) -> Client:
        """Alias for create_from_env."""

        return await cls.create_from_env(options)

    @classmethod
    async def build(cls, identifier: Identifier, options: ClientOptions | None = None) -> Client:
        """Create a client with an identifier (no signer)."""

        client = cls(options)
        await client._init(identifier)
        return client

    async def _init(self, identifier: Identifier) -> None:
        if self._client is not None:
            return

        self._identifier = identifier
        options = self._options
        apply_rust_log_from_options(options)
        host = options.resolved_api_url()
        gateway_host = options.gateway_host
        is_secure = host.startswith("https")

        api = await NativeBindings.connect_to_backend(
            host,
            gateway_host,
            is_secure,
            None,
            options.app_version,
            None,
            None,
        )

        history_sync_url = options.resolved_history_sync_url()
        if history_sync_url:
            sync_api = await NativeBindings.connect_to_backend(
                history_sync_url,
                gateway_host,
                history_sync_url.startswith("https"),
                None,
                options.app_version,
                None,
                None,
            )
        else:
            sync_api = api
            history_sync_url = None

        ffi_identifier = _identifier_to_ffi(identifier)
        inbox_id = await NativeBindings.get_inbox_id_for_identifier(api, ffi_identifier)
        nonce = options.nonce if options.nonce is not None else 0
        if inbox_id is None:
            inbox_id = NativeBindings.generate_inbox_id(ffi_identifier, nonce)

        db_path_option = options.db_path
        db_path: str | None
        if db_path_option == "auto":
            db_path = os.path.join(os.getcwd(), f"xmtp-{options.env}-{inbox_id}.db3")
        elif callable(db_path_option):
            db_path = db_path_option(inbox_id)
        else:
            db_path = db_path_option

        encryption_key = coerce_db_encryption_key(options.db_encryption_key)

        device_sync_mode = (
            NativeBindings.FfiSyncWorkerMode.DISABLED
            if options.disable_device_sync
            else NativeBindings.FfiSyncWorkerMode.ENABLED
        )

        try:
            self._client = await NativeBindings.create_client(
                api,
                sync_api,
                db_path,
                encryption_key,
                inbox_id,
                ffi_identifier,
                nonce,
                None,
                history_sync_url,
                device_sync_mode,
                None,
                None,
            )
        except Exception as exc:
            if _looks_like_db_error(exc):
                raise DatabaseOpenError(db_path, str(exc)) from exc
            raise

        conversations = Conversations(self, self._client.conversations())
        self._conversations = conversations
        self._preferences = Preferences(self, conversations)

    @property
    def inbox_id(self) -> str | None:
        """Inbox identifier for the user."""

        if self._client is None:
            return None
        return self._client.inbox_id()

    @property
    def installation_id(self) -> bytes | None:
        """Installation identifier for the user."""

        if self._client is None:
            return None
        return self._client.installation_id()

    @property
    def account_identifier(self) -> Identifier | None:
        """Return the account identifier used to initialize the client."""

        return self._identifier

    @property
    def is_registered(self) -> bool:
        """Return True if the user is registered with XMTP."""

        if self._client is None:
            return False
        return self._client.signature_request() is None

    @property
    def conversations(self) -> Conversations:
        """Conversation manager for the client."""

        if self._conversations is None:
            raise ClientNotInitializedError()
        return self._conversations

    @property
    def options(self) -> ClientOptions:
        """Return the client options."""

        return self._options

    @property
    def preferences(self) -> Preferences:
        """Preferences manager for the client."""

        if self._preferences is None:
            raise ClientNotInitializedError()
        return self._preferences

    async def register(self) -> None:
        """Register the user on XMTP."""

        if self._client is None:
            raise ClientNotInitializedError()
        if self._signer is None:
            raise SignerUnavailableError()

        signature_request = self._client.signature_request()
        if signature_request is None:
            return

        signature_text_result = cast(Any, signature_request).signature_text()
        if inspect.isawaitable(signature_text_result):
            signature_text = await signature_text_result
        else:
            signature_text = signature_text_result
        signature = await self._signer.sign_message(signature_text.encode())

        if self._signer.type == SignerType.SCW:
            address = await self._signer.get_address()
            chain_id = await self._signer.get_chain_id()
            block_number = await self._signer.get_block_number()
            await signature_request.add_scw_signature(signature, address, chain_id, block_number)
        else:
            await signature_request.add_ecdsa_signature(signature)

        await self._client.register_identity(signature_request)

    async def can_message(self, identifiers: list[Identifier]) -> dict[str, bool]:
        """Return a map of identifiers to messageability."""

        if self._client is None:
            raise ClientNotInitializedError()

        ffi_identifiers = [_identifier_to_ffi(identifier) for identifier in identifiers]
        result = await self._client.can_message(ffi_identifiers)
        return {item.identifier: can for item, can in result.items()}

    async def get_inbox_id_by_identifier(self, identifier: Identifier) -> str | None:
        """Resolve an identifier to an inbox id."""

        if self._client is None:
            raise ClientNotInitializedError()
        return await self._client.find_inbox_id(_identifier_to_ffi(identifier))

    def register_codec(self, codec: ContentCodec[ContentT]) -> None:
        """Register a content codec for encoding/decoding."""

        self._codecs[str(codec.content_type)] = cast(ContentCodec[object], codec)

    def register_codecs(self, codecs: Sequence[ContentCodec[ContentT]]) -> None:
        """Register multiple content codecs."""

        for codec in codecs:
            self.register_codec(codec)

    def codec_for(self, content_type: ContentTypeId | str) -> ContentCodec[object] | None:
        """Return the codec for a content type, if registered."""

        return self._codecs.get(str(content_type))

    def encode_content(self, content: ContentT, content_type: ContentTypeId | str) -> bytes:
        """Encode content for sending."""

        codec = self.codec_for(content_type)
        if codec is None:
            raise CodecNotFoundError(str(content_type))
        encoded = cast(ContentCodec[ContentT], codec).encode(content, self)
        return encoded.content

    def prepare_for_send(
        self,
        content: ContentT,
        content_type: ContentTypeId | str,
    ) -> tuple[bytes, NativeBindings.FfiSendMessageOpts | _SendMessageOpts]:
        """Prepare content for sending with codec-derived send options."""

        codec = self.codec_for(content_type)
        if codec is None:
            raise CodecNotFoundError(str(content_type))
        encoded = cast(ContentCodec[ContentT], codec).encode(content, self)
        should_push = cast(ContentCodec[ContentT], codec).should_push(content)
        send_opts = _default_send_opts(should_push=should_push)
        return encoded.content, send_opts

    def _decode_message(self, message: NativeBindings.FfiMessage) -> DecodedMessage[object]:
        if self._client is None:
            raise ClientNotInitializedError()

        decoded = self._client.enriched_message(message.id)
        content = self._decode_ffi_content(decoded.content())
        sent_at = datetime.fromtimestamp(decoded.sent_at_ns() / 1_000_000_000, tz=timezone.utc)
        content_type = _content_type_from_ffi(decoded.content_type_id())
        content_type_id = str(content_type) if content_type is not None else None
        return DecodedMessage(
            id=decoded.id(),
            conversation_id=decoded.conversation_id(),
            sender_inbox_id=decoded.sender_inbox_id(),
            sent_at=sent_at,
            content=content,
            content_type_id=content_type_id,
        )

    def _decode_ffi_content(self, content: NativeBindings.FfiDecodedMessageContent) -> object:
        if content.is_TEXT():
            text_payload = cast("NativeBindings.FfiDecodedMessageContent.TEXT", content)
            return text_payload[0].content
        if content.is_MARKDOWN():
            markdown_payload = cast("NativeBindings.FfiDecodedMessageContent.MARKDOWN", content)
            return markdown_payload[0].content
        if content.is_REACTION():
            from xmtp_content_type_reaction import Reaction, ReactionAction, ReactionSchema

            reaction_payload = cast("NativeBindings.FfiDecodedMessageContent.REACTION", content)[0]
            action = (
                ReactionAction.ADDED
                if reaction_payload.action == NativeBindings.FfiReactionAction.ADDED
                else ReactionAction.REMOVED
            )
            schema_map = {
                NativeBindings.FfiReactionSchema.UNICODE: ReactionSchema.UNICODE,
                NativeBindings.FfiReactionSchema.SHORTCODE: ReactionSchema.SHORTCODE,
                NativeBindings.FfiReactionSchema.CUSTOM: ReactionSchema.CUSTOM,
            }
            return Reaction(
                reference=reaction_payload.reference,
                reference_inbox_id=reaction_payload.reference_inbox_id or None,
                action=action,
                content=reaction_payload.content,
                schema=schema_map[reaction_payload.schema],
            )
        if content.is_REPLY():
            from xmtp_content_type_reply import Reply

            reply_payload = cast("NativeBindings.FfiDecodedMessageContent.REPLY", content)[0]
            encoded = _encoded_from_ffi(reply_payload.content)
            codec = self.codec_for(encoded.type_id)
            nested_content = codec.decode(encoded, self) if codec is not None else encoded.content
            return Reply(
                reference=reply_payload.reference,
                reference_inbox_id=reply_payload.reference_inbox_id or None,
                content=nested_content,
                content_type=encoded.type_id,
            )
        if content.is_REMOTE_ATTACHMENT():
            from xmtp_content_type_remote_attachment import RemoteAttachment

            attachment = cast(
                "NativeBindings.FfiDecodedMessageContent.REMOTE_ATTACHMENT",
                content,
            )[0]
            return RemoteAttachment(
                url=attachment.url,
                content_digest=attachment.content_digest,
                secret=attachment.secret,
                salt=attachment.salt,
                nonce=attachment.nonce,
                scheme=attachment.scheme,
                content_length=attachment.content_length,
                filename=attachment.filename,
            )
        if content.is_READ_RECEIPT():
            return {}
        if content.is_TRANSACTION_REFERENCE():
            from xmtp_content_type_transaction_reference import (
                TransactionMetadata,
                TransactionReference,
            )

            transaction_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.TRANSACTION_REFERENCE",
                content,
            )[0]
            metadata = None
            if transaction_payload.metadata is not None:
                metadata = TransactionMetadata(
                    transaction_type=transaction_payload.metadata.transaction_type,
                    currency=transaction_payload.metadata.currency,
                    amount=transaction_payload.metadata.amount,
                    decimals=transaction_payload.metadata.decimals,
                    from_address=transaction_payload.metadata.from_address,
                    to_address=transaction_payload.metadata.to_address,
                )
            return TransactionReference(
                namespace=transaction_payload.namespace,
                network_id=transaction_payload.network_id,
                reference=transaction_payload.reference,
                metadata=metadata,
            )
        if content.is_WALLET_SEND_CALLS():
            from xmtp_content_type_wallet_send_calls import (
                WalletCall,
                WalletCallMetadata,
                WalletSendCalls,
            )

            wallet_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.WALLET_SEND_CALLS",
                content,
            )[0]
            calls: list[WalletCall] = []
            for call in wallet_payload.calls:
                call_metadata = None
                if call.metadata is not None:
                    call_metadata = WalletCallMetadata(
                        description=call.metadata.description,
                        transaction_type=call.metadata.transaction_type,
                        extra=call.metadata.extra,
                    )
                calls.append(
                    WalletCall(
                        to=call.to,
                        data=call.data,
                        value=call.value,
                        gas=call.gas,
                        metadata=call_metadata,
                    )
                )
            return WalletSendCalls(
                version=wallet_payload.version,
                chain_id=wallet_payload.chain_id,
                from_address=wallet_payload._from,
                calls=calls,
                capabilities=wallet_payload.capabilities,
            )
        if content.is_GROUP_UPDATED():
            group_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.GROUP_UPDATED",
                content,
            )
            return group_payload[0]
        if content.is_ATTACHMENT():
            from xmtp_content_type_remote_attachment import Attachment

            attachment = cast(
                "NativeBindings.FfiDecodedMessageContent.ATTACHMENT",
                content,
            )[0]
            return Attachment(
                filename=attachment.filename,
                mime_type=attachment.mime_type,
                data=attachment.content,
            )
        if content.is_ACTIONS():
            actions_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.ACTIONS",
                content,
            )
            return actions_payload[0]
        if content.is_INTENT():
            intent_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.INTENT",
                content,
            )
            return intent_payload[0]
        if content.is_LEAVE_REQUEST():
            leave_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.LEAVE_REQUEST",
                content,
            )
            return leave_payload[0]
        if content.is_CUSTOM():
            custom_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.CUSTOM",
                content,
            )
            encoded = custom_payload[0]
            try:
                decoded = _encoded_from_ffi(encoded)
            except ValueError:
                return encoded
            codec = self.codec_for(decoded.type_id)
            if codec is None:
                return encoded
            return codec.decode(decoded, self)
        return content
