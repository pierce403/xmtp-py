# xmtp-py (python-sdk)

Unofficial Python SDK for the XMTP network.

This package mirrors the xmtp-js node SDK, adapted to Python idioms.

## Quick start

```python
from xmtp import Client
from xmtp.signers import create_signer
from xmtp.types import ClientOptions

signer = create_signer('0xYOUR_PRIVATE_KEY')
client = await Client.create(signer, ClientOptions(env='production', disable_history_sync=True))

dm = await client.conversations.new_dm('0x...')
await dm.send('Hello from Python!')
```

## Key management tips

- `create_signer()` expects a long-lived private key; store it outside source control.
- `XMTP_WALLET_KEY` can be used to load a signer from the environment.
- Keep `XMTP_DB_ENCRYPTION_KEY` and the database path stable to preserve installations.

## Configuration & troubleshooting

Endpoint overrides via env: `XMTP_API_URL`, `XMTP_HISTORY_SYNC_URL`, `XMTP_GATEWAY_HOST`, `XMTP_DISABLE_HISTORY_SYNC=1`.
Rust log override via env: `XMTP_RUST_LOG=error`.

History sync is disabled by default. Set `disable_history_sync=False` (and optionally
`history_sync_url`) to enable it.

If you see history sync gRPC errors, leave history sync disabled or set
`XMTP_DISABLE_HISTORY_SYNC=1`.

If Rust logs are too noisy, set `XMTP_RUST_LOG=error` or pass `rust_log="error"`
in `ClientOptions`.
