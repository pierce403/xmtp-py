"""XMTP client entry point."""

from __future__ import annotations

import inspect
import logging
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, TypeVar, cast

from xmtp_content_type_primitives import ContentCodec, ContentTypeId, EncodedContent

from xmtp.bindings import NativeBindings, check_binding_compatibility, get_bindings_version
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
from xmtp.version import __version__ as XMTP_VERSION

ContentT = TypeVar("ContentT")
logger = logging.getLogger(__name__)

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


def _is_ffi_variant(content: object, variant: str) -> bool:
    checker = getattr(content, f"is_{variant}", None)
    return callable(checker) and bool(checker())


def _looks_like_ffi_encoded_content(content: object) -> bool:
    return all(
        hasattr(content, field)
        for field in ("type_id", "parameters", "fallback", "compression", "content")
    )


def _unknown_content_type() -> ContentTypeId:
    return ContentTypeId(
        authority_id="unknown",
        type_id="unknown",
        version_major=0,
        version_minor=0,
    )


def _looks_like_db_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in _DB_ERROR_MARKERS)


def _callable_accepts_varargs(func: object) -> bool:
    try:
        signature = inspect.signature(cast(Callable[..., object], func))
    except (TypeError, ValueError):
        return True
    return any(
        parameter.kind == inspect.Parameter.VAR_POSITIONAL
        for parameter in signature.parameters.values()
    )


def _callable_parameter_names(func: object) -> list[str] | None:
    if _callable_accepts_varargs(func):
        return None
    try:
        signature = inspect.signature(cast(Callable[..., object], func))
    except (TypeError, ValueError):
        return None
    return [
        name
        for name, parameter in signature.parameters.items()
        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    ]


async def _connect_to_backend(
    host: str,
    gateway_host: str | None,
    is_secure: bool,
    app_version: str | None,
) -> object:
    connect = cast(Any, NativeBindings.connect_to_backend)
    parameter_names = _callable_parameter_names(connect)
    legacy_args = (host, gateway_host, is_secure, None, app_version, None, None)
    six_arg_candidates = (
        (host, is_secure, None, app_version, None, None),
        (host, gateway_host, is_secure, None, app_version, None),
    )

    if parameter_names is not None:
        if "gateway_host" in parameter_names:
            return await connect(*legacy_args[: len(parameter_names)])
        if len(parameter_names) == 6:
            return await connect(*six_arg_candidates[0])

    try:
        return await connect(*legacy_args)
    except TypeError as first_error:
        for args in six_arg_candidates:
            try:
                return await connect(*args)
            except TypeError:
                continue
        raise first_error


def _device_sync_mode(disabled: bool) -> object:
    mode_enum = getattr(NativeBindings, "FfiDeviceSyncMode", None)
    if mode_enum is None:
        mode_enum = NativeBindings.FfiSyncWorkerMode
    return mode_enum.DISABLED if disabled else mode_enum.ENABLED


def _make_db_options(db_path: str | None, encryption_key: bytes | None) -> object:
    db_options_cls = getattr(
        NativeBindings,
        "DbOptions",
        getattr(NativeBindings, "FfiDbOptions", None),
    )
    if db_options_cls is None:
        raise TypeError("DbOptions is unavailable in xmtp-bindings")

    parameter_names = _callable_parameter_names(db_options_cls)
    if parameter_names is not None:
        values: dict[str, object | None] = {}
        for name in parameter_names:
            if name in {"db", "db_path", "path"}:
                values[name] = db_path
            elif name in {"db_encryption_key", "encryption_key", "key"}:
                values[name] = encryption_key
        if values:
            return db_options_cls(**values)

    candidates = (
        {"db_path": db_path, "encryption_key": encryption_key},
        {"db": db_path, "encryption_key": encryption_key},
        {"path": db_path, "encryption_key": encryption_key},
        {"db_path": db_path, "db_encryption_key": encryption_key},
    )
    for kwargs in candidates:
        try:
            return db_options_cls(**kwargs)
        except TypeError:
            continue
    return db_options_cls(db_path, encryption_key)


async def _create_client(
    api: object,
    sync_api: object,
    db_path: str | None,
    encryption_key: bytes | None,
    inbox_id: str,
    ffi_identifier: object,
    nonce: int,
    history_sync_url: str | None,
    device_sync_mode: object,
) -> object:
    create_client = cast(Any, NativeBindings.create_client)
    parameter_names = _callable_parameter_names(create_client)
    legacy_args = (
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

    if parameter_names is None:
        return await create_client(*legacy_args)

    if len(parameter_names) == 12:
        return await create_client(*legacy_args)

    db_options = _make_db_options(db_path, encryption_key)
    values = {
        "api": api,
        "sync_api": sync_api,
        "db_options": db_options,
        "db": db_path,
        "db_path": db_path,
        "encryption_key": encryption_key,
        "inbox_id": inbox_id,
        "account_identifier": ffi_identifier,
        "identifier": ffi_identifier,
        "nonce": nonce,
        "legacy_signed_private_key_proto": None,
        "device_sync_server_url": history_sync_url,
        "history_sync_url": history_sync_url,
        "device_sync_mode": device_sync_mode,
        "sync_worker_mode": device_sync_mode,
        "allow_offline": None,
        "fork_recovery_opts": None,
    }
    missing = [name for name in parameter_names if name not in values]
    if missing:
        raise TypeError(f"Unsupported create_client parameters: {', '.join(missing)}")
    args = [values[name] for name in parameter_names]
    return await create_client(*args)


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

        check_binding_compatibility(XMTP_VERSION, NativeBindings)
        logger.debug(
            "Initializing XMTP client with xmtp=%s xmtp-bindings=%s",
            XMTP_VERSION,
            get_bindings_version() or "unknown",
        )

        self._identifier = identifier
        options = self._options
        apply_rust_log_from_options(options)
        host = options.resolved_api_url()
        gateway_host = options.gateway_host
        is_secure = host.startswith("https")

        api = await _connect_to_backend(host, gateway_host, is_secure, options.app_version)

        history_sync_url = options.resolved_history_sync_url()
        if history_sync_url:
            sync_api = await _connect_to_backend(
                history_sync_url,
                gateway_host,
                history_sync_url.startswith("https"),
                options.app_version,
            )
        else:
            sync_api = api
            history_sync_url = None

        ffi_identifier = _identifier_to_ffi(identifier)
        inbox_id = await cast(Any, NativeBindings.get_inbox_id_for_identifier)(
            api,
            ffi_identifier,
        )
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

        device_sync_mode = _device_sync_mode(options.disable_device_sync)

        try:
            self._client = cast(
                "NativeBindings.FfiXmtpClient",
                await _create_client(
                    api,
                    sync_api,
                    db_path,
                    encryption_key,
                    inbox_id,
                    ffi_identifier,
                    nonce,
                    history_sync_url,
                    device_sync_mode,
                ),
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

    def _content_type_for_decoded_body(self, content: object) -> ContentTypeId | None:
        if content is None:
            return None
        if _looks_like_ffi_encoded_content(content):
            try:
                return _encoded_from_ffi(cast("NativeBindings.FfiEncodedContent", content)).type_id
            except ValueError:
                return None
        if _is_ffi_variant(content, "TEXT"):
            from xmtp_content_type_text import ContentTypeText

            return ContentTypeText
        if _is_ffi_variant(content, "MARKDOWN"):
            from xmtp_content_type_markdown import ContentTypeMarkdown

            return ContentTypeMarkdown
        if _is_ffi_variant(content, "REACTION"):
            from xmtp_content_type_reaction import ContentTypeReaction

            return ContentTypeReaction
        if _is_ffi_variant(content, "REMOTE_ATTACHMENT"):
            from xmtp_content_type_remote_attachment import ContentTypeRemoteAttachment

            return ContentTypeRemoteAttachment
        if _is_ffi_variant(content, "MULTI_REMOTE_ATTACHMENT"):
            return ContentTypeId(
                authority_id="xmtp.org",
                type_id="multiRemoteStaticAttachment",
                version_major=1,
                version_minor=0,
            )
        if _is_ffi_variant(content, "ATTACHMENT"):
            from xmtp_content_type_remote_attachment import ContentTypeAttachment

            return ContentTypeAttachment
        if _is_ffi_variant(content, "READ_RECEIPT"):
            from xmtp_content_type_read_receipt import ContentTypeReadReceipt

            return ContentTypeReadReceipt
        if _is_ffi_variant(content, "TRANSACTION_REFERENCE"):
            from xmtp_content_type_transaction_reference import ContentTypeTransactionReference

            return ContentTypeTransactionReference
        if _is_ffi_variant(content, "WALLET_SEND_CALLS"):
            from xmtp_content_type_wallet_send_calls import ContentTypeWalletSendCalls

            return ContentTypeWalletSendCalls
        if _is_ffi_variant(content, "GROUP_UPDATED"):
            from xmtp_content_type_group_updated import ContentTypeGroupUpdated

            return ContentTypeGroupUpdated
        if _is_ffi_variant(content, "INTENT"):
            return ContentTypeId(
                authority_id="coinbase.com",
                type_id="intent",
                version_major=1,
                version_minor=0,
            )
        if _is_ffi_variant(content, "ACTIONS"):
            return ContentTypeId(
                authority_id="coinbase.com",
                type_id="actions",
                version_major=1,
                version_minor=0,
            )
        if _is_ffi_variant(content, "LEAVE_REQUEST"):
            return ContentTypeId(
                authority_id="xmtp.org",
                type_id="leave_request",
                version_major=1,
                version_minor=0,
            )
        if _is_ffi_variant(content, "DELETED_MESSAGE"):
            return ContentTypeId(
                authority_id="xmtp.org",
                type_id="deleteMessage",
                version_major=1,
                version_minor=0,
            )
        if _is_ffi_variant(content, "CUSTOM"):
            custom_payload = cast(Any, content)[0]
            try:
                return _encoded_from_ffi(custom_payload).type_id
            except ValueError:
                return None
        return None

    def _decode_ffi_content(self, content: object) -> object:
        if _looks_like_ffi_encoded_content(content):
            encoded = _encoded_from_ffi(cast("NativeBindings.FfiEncodedContent", content))
            codec = self.codec_for(encoded.type_id)
            return codec.decode(encoded, self) if codec is not None else encoded.content
        if _is_ffi_variant(content, "TEXT"):
            text_payload = cast("NativeBindings.FfiDecodedMessageContent.TEXT", content)
            return text_payload[0].content
        if _is_ffi_variant(content, "MARKDOWN"):
            markdown_payload = cast("NativeBindings.FfiDecodedMessageContent.MARKDOWN", content)
            return markdown_payload[0].content
        if _is_ffi_variant(content, "REACTION"):
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
        if _is_ffi_variant(content, "REPLY"):
            from xmtp_content_type_reply import Reply

            reply_payload = cast("NativeBindings.FfiDecodedMessageContent.REPLY", content)[0]
            nested_content = (
                None
                if reply_payload.content is None
                else self._decode_ffi_content(reply_payload.content)
            )
            content_type = self._content_type_for_decoded_body(reply_payload.content)
            return Reply(
                reference=reply_payload.reference,
                reference_inbox_id=reply_payload.reference_inbox_id or None,
                content=nested_content,
                content_type=content_type or _unknown_content_type(),
            )
        if _is_ffi_variant(content, "REMOTE_ATTACHMENT"):
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
                content_length=attachment.content_length or 0,
                filename=attachment.filename,
            )
        if _is_ffi_variant(content, "MULTI_REMOTE_ATTACHMENT"):
            multi_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.MULTI_REMOTE_ATTACHMENT",
                content,
            )
            return multi_payload[0]
        if _is_ffi_variant(content, "READ_RECEIPT"):
            return {}
        if _is_ffi_variant(content, "TRANSACTION_REFERENCE"):
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
        if _is_ffi_variant(content, "WALLET_SEND_CALLS"):
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
        if _is_ffi_variant(content, "GROUP_UPDATED"):
            group_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.GROUP_UPDATED",
                content,
            )
            return group_payload[0]
        if _is_ffi_variant(content, "ATTACHMENT"):
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
        if _is_ffi_variant(content, "ACTIONS"):
            actions_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.ACTIONS",
                content,
            )
            return actions_payload[0]
        if _is_ffi_variant(content, "INTENT"):
            intent_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.INTENT",
                content,
            )
            return intent_payload[0]
        if _is_ffi_variant(content, "LEAVE_REQUEST"):
            leave_payload = cast(
                "NativeBindings.FfiDecodedMessageContent.LEAVE_REQUEST",
                content,
            )
            return leave_payload[0]
        if _is_ffi_variant(content, "DELETED_MESSAGE"):
            deleted_payload = cast(
                Any,
                content,
            )
            return deleted_payload[0]
        if _is_ffi_variant(content, "CUSTOM"):
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
