"""Debug helpers for agent development."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xmtp import Client

if TYPE_CHECKING:
    from xmtp_agent.agent import Agent


def get_test_url(client: Client) -> str:
    """Return a URL to test the agent on xmtp.chat."""

    address = client.account_identifier.value if client.account_identifier else None
    env = client.options.env
    return f"http://xmtp.chat/{env}/dm/{address}"


@dataclass(slots=True)
class InstallationInfo:
    """Installation details for an XMTP client."""

    total_installations: int
    installation_id: str | None
    most_recent_installation_id: str | None
    is_most_recent: bool


def _installation_sort_key(installation: object) -> int:
    timestamp = getattr(installation, "client_timestamp_ns", None)
    if timestamp is None:
        return 0
    return int(timestamp)


async def get_installation_info(client: Client) -> InstallationInfo:
    """Return information about the client's installation state."""

    inbox_id = client.inbox_id
    installation_id = client.installation_id
    if inbox_id is None or installation_id is None:
        return InstallationInfo(
            total_installations=0,
            installation_id=None,
            most_recent_installation_id=None,
            is_most_recent=False,
        )

    inbox_state = await client.preferences.inbox_state(refresh_from_network=True)
    installations = list(getattr(inbox_state, "installations", []) or [])
    installations.sort(key=_installation_sort_key, reverse=True)

    installation_id_hex = installation_id.hex()
    most_recent = installations[0] if installations else None
    most_recent_hex = most_recent.id.hex() if most_recent else None
    is_most_recent = most_recent_hex == installation_id_hex if most_recent_hex else False

    return InstallationInfo(
        total_installations=len(installations),
        installation_id=installation_id_hex,
        most_recent_installation_id=most_recent_hex,
        is_most_recent=is_most_recent,
    )


async def log_details(agent: Agent) -> None:
    """Log basic agent details for debugging."""

    client = agent.client
    inbox_id = client.inbox_id
    installation_id = client.installation_id
    installation_id_display = installation_id.hex() if installation_id else None
    address = client.account_identifier.value if client.account_identifier else None
    env = client.options.env

    conversations = await client.conversations.list()
    inbox_state = await client.preferences.inbox_state()

    print("XMTP Agent Details")
    print(f"- Inbox ID: {inbox_id}")
    print(f"- Installation ID: {installation_id_display}")
    print(f"- Address: {address}")
    print(f"- Conversations: {len(conversations)}")
    print(f"- Installations: {len(inbox_state.installations)}")
    print(f"- Environment: {env}")
    print(f"- Test URL: {get_test_url(client)}")


__all__ = ["get_test_url", "get_installation_info", "log_details", "InstallationInfo"]
