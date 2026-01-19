import pytest

from xmtp.identifiers import Identifier, IdentifierKind
from xmtp_agent.agent import Agent
from xmtp_agent.debug import get_installation_info, get_test_url, log_details


class _Conversations:
    async def list(self):
        return [1, 2, 3]


class _Preferences:
    def __init__(self, installations):
        self._installations = installations

    async def inbox_state(self, refresh_from_network: bool = False):
        return type('InboxState', (), {'installations': self._installations})()


class _Installation:
    def __init__(self, installation_id: bytes, client_timestamp_ns: int | None):
        self.id = installation_id
        self.client_timestamp_ns = client_timestamp_ns


class _Client:
    def __init__(
        self,
        installations=None,
        installation_id: bytes | None = b'install',
        inbox_id: str | None = 'inbox',
    ) -> None:
        self.inbox_id = inbox_id
        self.installation_id = installation_id
        self.account_identifier = Identifier(kind=IdentifierKind.ETHEREUM, value='0xabc')
        self.options = type('Options', (), {'env': 'dev'})()
        self.conversations = _Conversations()
        self.preferences = _Preferences(installations if installations is not None else [1, 2])


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


@pytest.mark.asyncio
async def test_get_installation_info_most_recent() -> None:
    installations = [
        _Installation(b'\x01', 1),
        _Installation(b'\x02', 2),
    ]
    client = _Client(installations=installations, installation_id=b'\x02')
    info = await get_installation_info(client)
    assert info.total_installations == 2
    assert info.installation_id == '02'
    assert info.most_recent_installation_id == '02'
    assert info.is_most_recent is True


@pytest.mark.asyncio
async def test_get_installation_info_missing_ids() -> None:
    client = _Client(installations=[], installation_id=None, inbox_id=None)
    info = await get_installation_info(client)
    assert info.total_installations == 0
    assert info.installation_id is None
    assert info.most_recent_installation_id is None
    assert info.is_most_recent is False


@pytest.mark.asyncio
async def test_get_installation_info_missing_timestamp() -> None:
    installations = [_Installation(b'\x01', None)]
    client = _Client(installations=installations, installation_id=b'\x01')
    info = await get_installation_info(client)
    assert info.total_installations == 1
    assert info.installation_id == '01'
    assert info.most_recent_installation_id == '01'
    assert info.is_most_recent is True
