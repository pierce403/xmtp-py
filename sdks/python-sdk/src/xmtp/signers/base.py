"""Signer protocol for XMTP."""

from __future__ import annotations

from typing import Protocol


class Signer(Protocol):
    """Signer interface for XMTP clients."""

    async def get_address(self) -> str:
        """Return the wallet address for this signer."""

        ...

    async def sign_message(self, message: bytes) -> bytes:
        """Sign a message and return the signature bytes."""

        ...
