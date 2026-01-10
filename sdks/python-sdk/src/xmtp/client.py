"""XMTP client entry point."""

from __future__ import annotations

from xmtp.conversations import Conversations
from xmtp.errors import NotImplementedXmtpError
from xmtp.preferences import Preferences
from xmtp.signers.base import Signer
from xmtp.types import ClientOptions


class Client:
    """Main client for interacting with the XMTP network."""

    def __init__(
        self,
        signer: Signer,
        options: ClientOptions | None = None,
    ) -> None:
        self._signer = signer
        self._options = options or ClientOptions()
        self._conversations = Conversations()
        self._preferences = Preferences()

    @classmethod
    async def create(cls, signer: Signer, options: ClientOptions | None = None) -> 'Client':
        """Create a client with a signer."""

        raise NotImplementedXmtpError('Client.create not implemented')

    @classmethod
    async def build(cls, identifier: str, options: ClientOptions | None = None) -> 'Client':
        """Create a client with an identifier (no signer)."""

        raise NotImplementedXmtpError('Client.build not implemented')

    @property
    def inbox_id(self) -> str | None:
        """Inbox identifier for the user."""

        return None

    @property
    def installation_id(self) -> str | None:
        """Installation identifier for the user."""

        return None

    @property
    def is_registered(self) -> bool:
        """Return True if the user is registered with XMTP."""

        return False

    @property
    def conversations(self) -> Conversations:
        """Conversation manager for the client."""

        return self._conversations

    @property
    def preferences(self) -> Preferences:
        """Preferences manager for the client."""

        return self._preferences

    async def register(self) -> None:
        """Register the user on XMTP."""

        raise NotImplementedXmtpError('Client.register not implemented')

    async def can_message(self, identifier: str) -> bool:
        """Return True if the identifier can be messaged."""

        raise NotImplementedXmtpError('Client.can_message not implemented')

    async def get_inbox_id_by_identifier(self, identifier: str) -> str | None:
        """Resolve an identifier to an inbox id."""

        raise NotImplementedXmtpError('Client.get_inbox_id_by_identifier not implemented')
