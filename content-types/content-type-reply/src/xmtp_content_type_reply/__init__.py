"""Reply content type for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


def _bindings() -> Any:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return xmtpv3  # pragma: no cover - requires native bindings


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


def _content_type_to_ffi(content_type: ContentTypeId) -> Any:
    return _bindings().FfiContentTypeId(
        authority_id=content_type.authority_id,
        type_id=content_type.type_id,
        version_major=content_type.version_major,
        version_minor=content_type.version_minor,
    )


def _content_type_from_ffi(ffi: Any) -> ContentTypeId:
    if ffi is None:
        raise ValueError("Missing content type in encoded reply")
    return ContentTypeId(
        authority_id=ffi.authority_id,
        type_id=ffi.type_id,
        version_major=ffi.version_major,
        version_minor=ffi.version_minor,
    )


def _encoded_to_ffi(encoded: EncodedContent) -> Any:
    return _bindings().FfiEncodedContent(
        type_id=_content_type_to_ffi(encoded.type_id),
        parameters=encoded.parameters,
        fallback=encoded.fallback,
        compression=encoded.compression,
        content=encoded.content,
    )


def _encoded_from_ffi(encoded: Any) -> EncodedContent:
    return EncodedContent(
        type_id=_content_type_from_ffi(encoded.type_id),
        parameters=encoded.parameters,
        fallback=encoded.fallback,
        compression=encoded.compression,
        content=encoded.content,
    )


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
        decoded_content = _encoded_from_ffi(reply_payload.content)
        nested_content_type = decoded_content.type_id
        codec = registry.codec_for(nested_content_type)
        if codec is None:
            raise ValueError(f"Missing codec for content type {nested_content_type}")

        return Reply(
            reference=reply_payload.reference,
            reference_inbox_id=reply_payload.reference_inbox_id or None,
            content=codec.decode(decoded_content, registry),
            content_type=nested_content_type,
        )

    def fallback(self, content: Reply) -> str | None:
        if isinstance(content.content, str):
            return f'Replied with "{content.content}" to an earlier message'
        return "Replied to an earlier message"

    def should_push(self, content: Reply) -> bool:
        return True


__all__ = ["ContentTypeReply", "Reply", "ReplyCodec"]
