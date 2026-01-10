import pytest

from xmtp.identifiers import Identifier, IdentifierKind
from xmtp_agent.agent import Agent
from xmtp_agent.debug import get_test_url, log_details


class _Conversations:
    async def list(self):
        return [1, 2, 3]


class _Preferences:
    async def inbox_state(self):
        return type('InboxState', (), {'installations': [1, 2]})()


class _Client:
    def __init__(self) -> None:
        self.inbox_id = 'inbox'
        self.installation_id = b'install'
        self.account_identifier = Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc')
        self.options = type('Options', (), {'env': 'dev'})()
        self.conversations = _Conversations()
        self.preferences = _Preferences()


def test_get_test_url() -> None:
    client = _Client()
    assert get_test_url(client) == 'http://xmtp.chat/dev/dm/0xabc'

    client.account_identifier = None
    assert get_test_url(client) == 'http://xmtp.chat/dev/dm/None'


@pytest.mark.asyncio
async def test_log_details(capsys) -> None:
    agent = Agent(_Client())
    await log_details(agent)
    output = capsys.readouterr().out
    assert 'XMTP Agent Details' in output
    assert 'Inbox ID' in output
    assert 'Installations' in output
    assert 'Test URL' in output
