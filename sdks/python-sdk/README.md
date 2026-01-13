# xmtp-py (python-sdk)

Unofficial Python SDK for the XMTP network.

This package mirrors the xmtp-js node SDK, adapted to Python idioms.

## Quick start

```python
from xmtp import Client
from xmtp.signers import create_signer
from xmtp.types import ClientOptions

signer = create_signer('0xYOUR_PRIVATE_KEY')
client = await Client.create(signer, ClientOptions(env='dev'))

dm = await client.conversations.new_dm('0x...')
await dm.send('Hello from Python!')
```

## Key management tips

- `create_signer()` expects a long-lived private key; store it outside source control.
- `XMTP_WALLET_KEY` can be used to load a signer from the environment.
- Keep `XMTP_DB_ENCRYPTION_KEY` and the database path stable to preserve installations.
