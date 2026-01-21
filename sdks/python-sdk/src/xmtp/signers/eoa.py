"""Externally owned account signer."""

from __future__ import annotations

from typing import cast

from eth_account import Account
from eth_account.messages import encode_defunct

from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.signers.base import Signer, SignerType


class EoaSigner(Signer):
    """EOA signer created from a private key."""

    def __init__(self, private_key: str) -> None:
        self._private_key = private_key
        self._account = Account.from_key(private_key)
        self.type = SignerType.EOA

    async def get_address(self) -> str:
        """Return the wallet address for this signer."""

        return cast(str, self._account.address)

    async def get_identifier(self) -> Identifier:
        """Return the XMTP identifier for this signer."""

        return Identifier(kind=IdentifierKind.ETHEREUM, value=self._account.address)

    async def sign_message(self, message: bytes) -> bytes:
        """Sign a message and return the signature bytes."""

        signable = encode_defunct(message)
        signed = self._account.sign_message(signable)
        return cast(bytes, signed.signature)

    async def get_chain_id(self) -> int:
        """Return the chain ID (not applicable for EOA)."""

        raise ValueError("EOA signer does not support chain_id")

    async def get_block_number(self) -> int | None:
        """Return block number (not applicable for EOA)."""

        return None


def create_signer(private_key: str) -> EoaSigner:
    """Create an EOA signer from a private key string."""

    return EoaSigner(private_key)
