"""User preferences management."""

from __future__ import annotations

from xmtp.errors import NotImplementedXmtpError


class Preferences:
    """Manage user preferences for the XMTP client."""

    async def refresh(self) -> None:
        """Refresh preferences from the network."""

        raise NotImplementedXmtpError('Preferences.refresh not implemented')
