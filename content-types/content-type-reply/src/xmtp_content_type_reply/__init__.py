"""Reply content type for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, cast

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


class _FfiContentTypeId(Protocol):
    def __init__(
        self,
        *,
        authority_id: str,
        type_id: str,
        version_major: int,
        version_minor: int,
    ) -> None: ...

    authority_id: str
    type_id: str
    version_major: int
    version_minor: int


class _FfiEncodedContent(Protocol):
    def __init__(
        self,
        *,
        type_id: _FfiContentTypeId,
        parameters: dict[str, str],
        fallback: str | None,
        compression: int | None,
        content: bytes,
    ) -> None: ...

    type_id: _FfiContentTypeId | None
    parameters: dict[str, str]
    fallback: str | None
    compression: int | None
    content: bytes


class _FfiReply(Protocol):
    def __init__(
        self,
        *,
        reference: str,
        reference_inbox_id: str | None,
        content: _FfiEncodedContent,
    ) -> None: ...

    reference: str
    reference_inbox_id: str | None
    content: _FfiEncodedContent


class _Bindings(Protocol):
    FfiContentTypeId: type[_FfiContentTypeId]
    FfiEncodedContent: type[_FfiEncodedContent]
    FfiReply: type[_FfiReply]

    def encode_reply(self, payload: _FfiReply) -> bytes: ...

    def decode_reply(self, data: bytes) -> _FfiReply: ...


def _bindings() -> _Bindings:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return cast(_Bindings, xmtpv3)  # pragma: no cover - requires native bindings


ContentTypeReply = ContentTypeId(
    authority_id="xmtp.org",
    type_id="reply",
    version_major=1,
    version_minor=0,
)


@dataclass(slots=True)
class Reply:
    """Reply content wrapper."""

    reference: str
    reference_inbox_id: str | None
    content: Any
    content_type: ContentTypeId


def _content_type_to_ffi(content_type: ContentTypeId) -> _FfiContentTypeId:
    return _bindings().FfiContentTypeId(
        authority_id=content_type.authority_id,
        type_id=content_type.type_id,
        version_major=content_type.version_major,
        version_minor=content_type.version_minor,
    )


def _content_type_from_ffi(ffi: _FfiContentTypeId | None) -> ContentTypeId:
    if ffi is None:
        raise ValueError("Missing content type in encoded reply")
    return ContentTypeId(
        authority_id=ffi.authority_id,
        type_id=ffi.type_id,
        version_major=ffi.version_major,
        version_minor=ffi.version_minor,
    )


def _encoded_to_ffi(encoded: EncodedContent) -> _FfiEncodedContent:
    return _bindings().FfiEncodedContent(
        type_id=_content_type_to_ffi(encoded.type_id),
        parameters=encoded.parameters,
        fallback=encoded.fallback,
        compression=encoded.compression,
        content=encoded.content,
    )


def _encoded_from_ffi(encoded: _FfiEncodedContent) -> EncodedContent:
    return EncodedContent(
        type_id=_content_type_from_ffi(encoded.type_id),
        parameters=encoded.parameters,
        fallback=encoded.fallback,
        compression=encoded.compression,
        content=encoded.content,
    )


def _looks_like_ffi_encoded_content(content: object) -> bool:
    return all(
        hasattr(content, field)
        for field in ("type_id", "parameters", "fallback", "compression", "content")
    )


def _is_ffi_variant(content: object, variant: str) -> bool:
    checker = getattr(content, f"is_{variant}", None)
    return callable(checker) and bool(checker())


def _unknown_content_type() -> ContentTypeId:
    return ContentTypeId(
        authority_id="unknown",
        type_id="unknown",
        version_major=0,
        version_minor=0,
    )


def _decoded_body_content_type(content: object) -> ContentTypeId:
    if _is_ffi_variant(content, "TEXT"):
        from xmtp_content_type_text import ContentTypeText

        return ContentTypeText
    if _is_ffi_variant(content, "MARKDOWN"):
        from xmtp_content_type_markdown import ContentTypeMarkdown

        return ContentTypeMarkdown
    if _is_ffi_variant(content, "REACTION"):
        from xmtp_content_type_reaction import ContentTypeReaction

        return ContentTypeReaction
    return _unknown_content_type()


def _decode_decoded_body(content: object) -> object:
    if _is_ffi_variant(content, "TEXT"):
        return cast(Any, content)[0].content
    if _is_ffi_variant(content, "MARKDOWN"):
        return cast(Any, content)[0].content
    if _is_ffi_variant(content, "REACTION"):
        from xmtp_content_type_reaction import Reaction, ReactionAction, ReactionSchema

        reaction_payload = cast(Any, content)[0]
        bindings = cast(Any, _bindings())
        action = (
            ReactionAction.ADDED
            if reaction_payload.action == bindings.FfiReactionAction.ADDED
            else ReactionAction.REMOVED
        )
        schema_map = {
            bindings.FfiReactionSchema.UNICODE: ReactionSchema.UNICODE,
            bindings.FfiReactionSchema.SHORTCODE: ReactionSchema.SHORTCODE,
            bindings.FfiReactionSchema.CUSTOM: ReactionSchema.CUSTOM,
        }
        return Reaction(
            reference=reaction_payload.reference,
            reference_inbox_id=reaction_payload.reference_inbox_id or None,
            action=action,
            content=reaction_payload.content,
            schema=schema_map[reaction_payload.schema],
        )
    return content


class ReplyCodec(ContentCodec[Reply]):
    """Codec for reply messages."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeReply

    def encode(self, content: Reply, registry: CodecRegistry | None = None) -> EncodedContent:
        if registry is None:
            raise ValueError("Codec registry required to encode replies")

        codec = registry.codec_for(content.content_type)
        if codec is None:
            raise ValueError(f"Missing codec for content type {content.content_type}")

        encoded_content = codec.encode(content.content, registry)
        reply_payload = _bindings().FfiReply(
            reference=content.reference,
            reference_inbox_id=content.reference_inbox_id,
            content=_encoded_to_ffi(encoded_content),
        )
        reply_bytes = _bindings().encode_reply(reply_payload)
        parameters = {
            "contentType": str(content.content_type),
            "reference": content.reference,
        }
        if content.reference_inbox_id:
            parameters["referenceInboxId"] = content.reference_inbox_id
        return EncodedContent(
            type_id=self.content_type,
            parameters=parameters,
            content=reply_bytes,
        )

    def decode(self, content: EncodedContent, registry: CodecRegistry | None = None) -> Reply:
        if registry is None:
            raise ValueError("Codec registry required to decode replies")

        reply_payload = _bindings().decode_reply(content.content)
        if _looks_like_ffi_encoded_content(reply_payload.content):
            decoded_content = _encoded_from_ffi(reply_payload.content)
            nested_content_type = decoded_content.type_id
            codec = registry.codec_for(nested_content_type)
            if codec is None:
                raise ValueError(f"Missing codec for content type {nested_content_type}")
            nested_content = codec.decode(decoded_content, registry)
        else:
            nested_content_type = _decoded_body_content_type(reply_payload.content)
            nested_content = _decode_decoded_body(reply_payload.content)

        return Reply(
            reference=reply_payload.reference,
            reference_inbox_id=reply_payload.reference_inbox_id or None,
            content=nested_content,
            content_type=nested_content_type,
        )

    def fallback(self, content: Reply) -> str | None:
        if isinstance(content.content, str):
            return f'Replied with "{content.content}" to an earlier message'
        return "Replied to an earlier message"

    def should_push(self, content: Reply) -> bool:
        return True


__all__ = ["ContentTypeReply", "Reply", "ReplyCodec"]
