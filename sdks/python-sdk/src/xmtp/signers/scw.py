"""Smart contract wallet signer."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.signers.base import Signer, SignerType


class ScwSigner(Signer):
    """Signer for smart contract wallets."""

    def __init__(
        self,
        address: str,
        sign_message: Callable[[bytes], Awaitable[bytes]],
        chain_id: int,
        block_number: int | None = None,
    ) -> None:
        self._address = address
        self._sign_message = sign_message
        self._chain_id = chain_id
        self._block_number = block_number
        self.type = SignerType.SCW

    async def get_address(self) -> str:
        """Return the wallet address for this signer."""

        return self._address

    async def get_identifier(self) -> Identifier:
        """Return the XMTP identifier for this signer."""

        return Identifier(kind=IdentifierKind.ETHEREUM, value=self._address)

    async def sign_message(self, message: bytes) -> bytes:
        """Sign a message and return the signature bytes."""

        return await self._sign_message(message)

    async def get_chain_id(self) -> int:
        """Return the chain ID for SCW signatures."""

        return self._chain_id

    async def get_block_number(self) -> int | None:
        """Return the block number for SCW signatures, if any."""

        return self._block_number
