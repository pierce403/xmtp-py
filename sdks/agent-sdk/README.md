# xmtp-agent-sdk

Unofficial XMTP agent SDK for Python.

This package provides an event-driven agent framework inspired by xmtp-js.

## Quick start

```python
from xmtp_agent import Agent
from xmtp_agent.user import create_signer, create_user

user = create_user()
signer = create_signer(user)
agent = await Agent.create(signer)

@agent.on('text')
async def on_text(ctx):
    await ctx.send_text('Hello from my agent!')

await agent.start()
```

## Key management tips

- `create_user()` generates a fresh private key each run; persist the key if you want a stable inbox.
- `Agent.create_from_env()` loads `XMTP_WALLET_KEY`; prefer env vars or a secrets manager over hardcoding.
- Keep your database directory and encryption key stable to avoid spinning up excess installations.

## Configuration & troubleshooting

Endpoint overrides via env: `XMTP_API_URL`, `XMTP_HISTORY_SYNC_URL`, `XMTP_GATEWAY_HOST`, `XMTP_DISABLE_HISTORY_SYNC=1`.
Rust log override via env: `XMTP_RUST_LOG=error`.

History sync is disabled by default. Set `disable_history_sync=False` (and optionally
`history_sync_url`) to enable it.

If you see history sync gRPC errors, leave history sync disabled or set
`XMTP_DISABLE_HISTORY_SYNC=1`.

If Rust logs are too noisy, set `XMTP_RUST_LOG=error` or pass `rust_log="error"`
in `ClientOptions`.
