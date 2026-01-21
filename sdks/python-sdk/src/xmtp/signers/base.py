"""Signer protocol for XMTP."""

from __future__ import annotations

from enum import Enum
from typing import Protocol

from xmtp.identifiers import Identifier


class SignerType(str, Enum):
    """Supported signer types."""

    EOA = "EOA"
    SCW = "SCW"


class Signer(Protocol):
    """Signer interface for XMTP clients."""

    type: SignerType

    async def get_address(self) -> str:
        """Return the wallet address for this signer."""

        ...

    async def get_identifier(self) -> Identifier:
        """Return the XMTP identifier for this signer."""

        ...

    async def sign_message(self, message: bytes) -> bytes:
        """Sign a message and return the signature bytes."""

        ...

    async def get_chain_id(self) -> int:
        """Return the chain ID (SCW only)."""

        ...

    async def get_block_number(self) -> int | None:
        """Return the block number for SCW signatures, if needed."""

        ...
