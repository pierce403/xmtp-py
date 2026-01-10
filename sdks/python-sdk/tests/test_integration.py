import os

import pytest

pytestmark = pytest.mark.integration

pytest.importorskip('xmtp_bindings')

from xmtp import Client
from xmtp.env import load_client_options_from_env, load_signer_from_env


@pytest.mark.asyncio
async def test_integration_can_connect() -> None:
    if not os.getenv('XMTP_INTEGRATION_TESTS'):
        pytest.skip('XMTP_INTEGRATION_TESTS not set')

    signer = load_signer_from_env()
    options = load_client_options_from_env()

    client = await Client.create(signer, options)
    assert client.inbox_id is not None
