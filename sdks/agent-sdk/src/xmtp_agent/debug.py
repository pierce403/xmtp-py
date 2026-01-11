"""Debug helpers for agent development."""

from __future__ import annotations

from xmtp import Client

from xmtp_agent.agent import Agent


def get_test_url(client: Client) -> str:
    """Return a URL to test the agent on xmtp.chat."""

    address = client.account_identifier.value if client.account_identifier else None
    env = client.options.env
    return f'http://xmtp.chat/{env}/dm/{address}'


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

    print('XMTP Agent Details')
    print(f'- Inbox ID: {inbox_id}')
    print(f'- Installation ID: {installation_id_display}')
    print(f'- Address: {address}')
    print(f'- Conversations: {len(conversations)}')
    print(f'- Installations: {len(inbox_state.installations)}')
    print(f'- Environment: {env}')
    print(f'- Test URL: {get_test_url(client)}')


__all__ = ['get_test_url', 'log_details']
