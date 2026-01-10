import pytest

pytest.importorskip('xmtp_bindings')

from xmtp import Client
from xmtp_agent.agent import Agent


def test_agent_on_registers_handler() -> None:
    agent = Agent(Client())

    def handler(ctx):
        return None

    returned = agent.on('message', handler)
    assert returned is handler
