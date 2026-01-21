"""Wallet send calls content type for XMTP."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Protocol, cast

from xmtp_content_type_primitives import (
    CodecRegistry,
    ContentCodec,
    ContentTypeId,
    EncodedContent,
)


class _FfiWalletCallMetadata(Protocol):
    def __init__(
        self,
        *,
        description: str,
        transaction_type: str,
        extra: dict[str, str],
    ) -> None: ...

    description: str
    transaction_type: str
    extra: dict[str, str]


class _FfiWalletCall(Protocol):
    def __init__(
        self,
        *,
        to: str | None,
        data: str | None,
        value: str | None,
        gas: str | None,
        metadata: _FfiWalletCallMetadata | None,
    ) -> None: ...

    to: str | None
    data: str | None
    value: str | None
    gas: str | None
    metadata: _FfiWalletCallMetadata | None


class _FfiWalletSendCalls(Protocol):
    def __init__(
        self,
        *,
        version: str,
        chain_id: str,
        _from: str,
        calls: list[_FfiWalletCall],
        capabilities: dict[str, str] | None,
    ) -> None: ...

    version: str
    chain_id: str
    _from: str
    calls: list[_FfiWalletCall]
    capabilities: dict[str, str] | None


class _Bindings(Protocol):
    FfiWalletCallMetadata: type[_FfiWalletCallMetadata]
    FfiWalletCall: type[_FfiWalletCall]
    FfiWalletSendCalls: type[_FfiWalletSendCalls]

    def encode_wallet_send_calls(self, payload: _FfiWalletSendCalls) -> bytes: ...

    def decode_wallet_send_calls(self, data: bytes) -> _FfiWalletSendCalls: ...


def _bindings() -> _Bindings:  # pragma: no cover - requires native bindings
    from xmtp_bindings import xmtpv3  # pragma: no cover - requires native bindings

    return cast(_Bindings, xmtpv3)  # pragma: no cover - requires native bindings


ContentTypeWalletSendCalls = ContentTypeId(
    authority_id="xmtp.org",
    type_id="walletSendCalls",
    version_major=1,
    version_minor=0,
)


@dataclass(slots=True)
class WalletCallMetadata:
    """Metadata describing a wallet call."""

    description: str
    transaction_type: str
    extra: dict[str, str]


@dataclass(slots=True)
class WalletCall:
    """Wallet call fields."""

    to: str | None
    data: str | None
    value: str | None
    gas: str | None
    metadata: WalletCallMetadata | None = None


@dataclass(slots=True)
class WalletSendCalls:
    """Wallet send calls payload."""

    version: str
    chain_id: str
    from_address: str
    calls: list[WalletCall]
    capabilities: dict[str, str] | None = None


class WalletSendCallsCodec(ContentCodec[WalletSendCalls]):
    """Codec for wallet send calls."""

    @property
    def content_type(self) -> ContentTypeId:
        return ContentTypeWalletSendCalls

    def encode(
        self,
        content: WalletSendCalls,
        registry: CodecRegistry | None = None,
    ) -> EncodedContent:
        calls = []
        for call in content.calls:
            metadata = None
            if call.metadata is not None:
                metadata = _bindings().FfiWalletCallMetadata(
                    description=call.metadata.description,
                    transaction_type=call.metadata.transaction_type,
                    extra=call.metadata.extra,
                )
            calls.append(
                _bindings().FfiWalletCall(
                    to=call.to,
                    data=call.data,
                    value=call.value,
                    gas=call.gas,
                    metadata=metadata,
                )
            )
        payload = _bindings().FfiWalletSendCalls(
            version=content.version,
            chain_id=content.chain_id,
            _from=content.from_address,
            calls=calls,
            capabilities=content.capabilities,
        )
        encoded = _bindings().encode_wallet_send_calls(payload)
        return EncodedContent(type_id=self.content_type, parameters={}, content=encoded)

    def decode(
        self,
        content: EncodedContent,
        registry: CodecRegistry | None = None,
    ) -> WalletSendCalls:
        payload = _bindings().decode_wallet_send_calls(content.content)
        calls: list[WalletCall] = []
        for call in payload.calls:
            metadata = None
            if call.metadata is not None:
                metadata = WalletCallMetadata(
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
                    metadata=metadata,
                )
            )
        return WalletSendCalls(
            version=payload.version,
            chain_id=payload.chain_id,
            from_address=payload._from,
            calls=calls,
            capabilities=payload.capabilities,
        )

    def fallback(self, content: WalletSendCalls) -> str | None:
        return f"[Transaction request generated]: {json.dumps(asdict(content))}"

    def should_push(self, content: WalletSendCalls) -> bool:
        return True


__all__ = [
    "ContentTypeWalletSendCalls",
    "WalletCall",
    "WalletCallMetadata",
    "WalletSendCalls",
    "WalletSendCallsCodec",
]
