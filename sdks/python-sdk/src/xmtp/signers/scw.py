"""Smart contract wallet signer."""

from __future__ import annotations

from xmtp.errors import NotImplementedXmtpError
from xmtp.signers.base import Signer


class ScwSigner(Signer):
    """Signer for smart contract wallets."""

    async def get_address(self) -> str:
        """Return the wallet address for this signer."""

        raise NotImplementedXmtpError('ScwSigner.get_address not implemented')

    async def sign_message(self, message: bytes) -> bytes:
        """Sign a message and return the signature bytes."""

        raise NotImplementedXmtpError('ScwSigner.sign_message not implemented')
