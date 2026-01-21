"""Transaction reference content type for XMTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


class _FfiTransactionMetadata(Protocol):
    def __init__(
        self,
        *,
        transaction_type: str,
        currency: str,
        amount: float,
        decimals: int,
        from_address: str,
        to_address: str,
    ) -> None: ...

    transaction_type: str
    currency: str
    amount: float
    decimals: int
    from_address: str
    to_address: str


class _FfiTransactionReference(Protocol):
    def __init__(
        self,
        *,
        namespace: str | None,
        network_id: str,
        reference: str,
        metadata: _FfiTransactionMetadata | None,
    ) -> None: ...

    namespace: str | None
    network_id: str
    reference: str
    metadata: _FfiTransactionMetadata | None


class _Bindings(Protocol):
    FfiTransactionMetadata: type[_FfiTransactionMetadata]
    FfiTransactionReference: type[_FfiTransactionReference]

    def encode_transaction_reference(self, payload: _FfiTransactionReference) -> bytes: ...

    def decode_transaction_reference(self, data: bytes) -> _FfiTransactionReference: ...


def _bindings() -> _Bindings:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return cast(_Bindings, xmtpv3)  # pragma: no cover - requires native bindings


ContentTypeTransactionReference = ContentTypeId(
    authority_id="xmtp.org",
    type_id="transactionReference",
    version_major=1,
    version_minor=0,
)


@dataclass(slots=True)
class TransactionMetadata:
    """Optional transaction metadata."""

    transaction_type: str
    currency: str
    amount: float
    decimals: int
    from_address: str
    to_address: str


@dataclass(slots=True)
class TransactionReference:
    """Transaction reference content."""

    namespace: str | None
    network_id: str | int
    reference: str
    metadata: TransactionMetadata | None = None


class TransactionReferenceCodec(ContentCodec[TransactionReference]):
    """Codec for transaction references."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeTransactionReference

    def encode(
        self,
        content: TransactionReference,
        registry: CodecRegistry | None = None,
    ) -> EncodedContent:
        metadata = None
        if content.metadata is not None:
            metadata = _bindings().FfiTransactionMetadata(
                transaction_type=content.metadata.transaction_type,
                currency=content.metadata.currency,
                amount=content.metadata.amount,
                decimals=content.metadata.decimals,
                from_address=content.metadata.from_address,
                to_address=content.metadata.to_address,
            )
        payload = _bindings().FfiTransactionReference(
            namespace=content.namespace,
            network_id=str(content.network_id),
            reference=content.reference,
            metadata=metadata,
        )
        encoded = _bindings().encode_transaction_reference(payload)
        return EncodedContent(type_id=self.content_type, parameters={}, content=encoded)

    def decode(
        self,
        content: EncodedContent,
        registry: CodecRegistry | None = None,
    ) -> TransactionReference:
        payload = _bindings().decode_transaction_reference(content.content)
        metadata = None
        if payload.metadata is not None:
            metadata = TransactionMetadata(
                transaction_type=payload.metadata.transaction_type,
                currency=payload.metadata.currency,
                amount=payload.metadata.amount,
                decimals=payload.metadata.decimals,
                from_address=payload.metadata.from_address,
                to_address=payload.metadata.to_address,
            )
        return TransactionReference(
            namespace=payload.namespace,
            network_id=payload.network_id,
            reference=payload.reference,
            metadata=metadata,
        )

    def fallback(self, content: TransactionReference) -> str | None:
        if content.reference:
            return (
                "[Crypto transaction] Use a blockchain explorer to learn more "
                f"using the transaction hash: {content.reference}"
            )
        return "Crypto transaction"

    def should_push(self, content: TransactionReference) -> bool:
        return True


__all__ = [
    "ContentTypeTransactionReference",
    "TransactionMetadata",
    "TransactionReference",
    "TransactionReferenceCodec",
]
