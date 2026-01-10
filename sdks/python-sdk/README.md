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
