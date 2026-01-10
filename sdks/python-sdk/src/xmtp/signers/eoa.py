"""Externally owned account signer."""

from __future__ import annotations

from xmtp.errors import NotImplementedXmtpError
from xmtp.signers.base import Signer


class EoaSigner(Signer):
    """EOA signer created from a private key."""

    def __init__(self, private_key: str) -> None:
        self._private_key = private_key

    async def get_address(self) -> str:
        """Return the wallet address for this signer."""

        raise NotImplementedXmtpError('EoaSigner.get_address not implemented')

    async def sign_message(self, message: bytes) -> bytes:
        """Sign a message and return the signature bytes."""

        raise NotImplementedXmtpError('EoaSigner.sign_message not implemented')


def create_signer(private_key: str) -> EoaSigner:
    """Create an EOA signer from a private key string."""

    return EoaSigner(private_key)
