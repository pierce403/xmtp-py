# xmtp

Unofficial Python client SDKs for the XMTP network.

Primary goal: feature parity with xmtp-js.

This is a community project that mirrors the structure and interfaces of the official [xmtp-js](https://github.com/xmtp/xmtp-js) SDK, adapted for Python.

## What's inside?

### SDKs

- [`python-sdk`](sdks/python-sdk): XMTP client SDK for Python
- [`agent-sdk`](sdks/agent-sdk): XMTP agent SDK for Python (event-driven, middleware-powered)

### Content types

- [`content-type-primitives`](content-types/content-type-primitives): Primitives for building custom XMTP content types
- [`content-type-group-updated`](content-types/content-type-group-updated): Content type for group update messages
- [`content-type-reaction`](content-types/content-type-reaction): Content type for reactions to messages
- [`content-type-read-receipt`](content-types/content-type-read-receipt): Content type for read receipts
- [`content-type-remote-attachment`](content-types/content-type-remote-attachment): Content type for file attachments stored off-network
- [`content-type-reply`](content-types/content-type-reply): Content type for direct replies to messages
- [`content-type-text`](content-types/content-type-text): Content type for plain text messages
- [`content-type-transaction-reference`](content-types/content-type-transaction-reference): Content type for on-chain transaction references
- [`content-type-markdown`](content-types/content-type-markdown): Content type for markdown-formatted messages
- [`content-type-wallet-send-calls`](content-types/content-type-wallet-send-calls): Content type for wallet transaction requests

## Requirements

- Python 3.10+
- libxmtp bindings >= 1.7.0-r3

## Installation

```bash
pip install xmtp
```

This installs the client SDK, agent SDK, and built-in content types in one package.

### Install from GitHub main

```bash
pip install "xmtp @ git+https://github.com/pierce403/xmtp-py.git@main"
```

### From source (dev)

Clone the repo and install into a virtualenv. Install the bindings first so
the local editable package can resolve them:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip

pip install -e bindings/python
pip install -e ".[dev]"
```

## Quick start

### Agent SDK (recommended)

```python
import asyncio
import xmtp

from xmtp_agent import Agent
from xmtp_agent.name_resolver import create_name_resolver
from xmtp_agent.user import create_user, create_signer
from xmtp.types import ClientOptions, LogLevel

recipient = "deanpierce.eth"


async def main() -> None:
    # Create a user and signer
    user = create_user()
    signer = create_signer(user)

    # Create the agent
    agent = await Agent.create(
        signer,
        ClientOptions(
            env="dev",
            disable_history_sync=True,
            logging_level=LogLevel.WARN,
            db_path=None,
        ),
    )

    # Resolve the recipient and send a message
    resolver = create_name_resolver()
    address = await resolver(recipient)
    if address is None:
        raise ValueError(f'Could not resolve address for "{recipient}"')

    dm = await agent.client.conversations.new_dm(address)
    await dm.send(f"Hello from xmtp-py {xmtp.__version__}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Python SDK (client)

```python
import asyncio
import xmtp

from xmtp import Client
from xmtp.signers import create_signer
from xmtp.types import ClientOptions, LogLevel
from xmtp_agent.name_resolver import create_name_resolver

recipient = "deanpierce.eth"


async def main() -> None:
    signer = create_signer(private_key)
    client = await Client.create(
        signer,
        ClientOptions(
            env="dev",
            disable_history_sync=True,
            logging_level=LogLevel.WARN,
        ),
    )

    resolver = create_name_resolver()
    address = await resolver(recipient)
    if address is None:
        raise ValueError(f'Could not resolve address for "{recipient}"')

    dm = await client.conversations.new_dm(address)
    await dm.send(f"Hello from xmtp-py {xmtp.__version__}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key management tips

- `create_user()` generates an in-memory key; persist the private key yourself if you want a stable inbox across restarts.
- Prefer `XMTP_WALLET_KEY` and `XMTP_DB_ENCRYPTION_KEY` in environment variables or a secrets manager; never commit them to git.
- Use a stable `db_path` and keep the database directory between runs. Losing it creates a new installation and can hit installation limits.
- For production, wrap a hardware wallet or KMS signer by implementing the `Signer` protocol instead of storing raw keys.

## Configuration & troubleshooting

History sync is disabled by default. To enable it, pass
`disable_history_sync=False` (and optionally `history_sync_url`) in `ClientOptions`,
or set `XMTP_HISTORY_SYNC_URL`.

Endpoint overrides via env:
- `XMTP_ENV`, `XMTP_API_URL`, `XMTP_HISTORY_SYNC_URL`, `XMTP_GATEWAY_HOST`
- `XMTP_DISABLE_HISTORY_SYNC=1` to force identity calls through the primary API
- `XMTP_RUST_LOG` to override Rust logging (defaults to `off`)

Common issues:
- **Missing `libxmtpv3.so`**: install will build it automatically, but you need Rust (`cargo`) and `git`. See `bindings/python/README.md` for overrides. If no prebuilt wheels are available, `pip install xmtp` will fall back to a source build.
- **History sync gRPC errors**: leave history sync disabled, or set `XMTP_DISABLE_HISTORY_SYNC=1`. To re-enable, pass `disable_history_sync=False` (and optionally `history_sync_url`) in `ClientOptions`.
- **Gateway host errors**: `gateway_host` is an advanced setting; only set it when you have a gateway that supports XMTP gRPC.
- **Noisy Rust logs**: set `XMTP_RUST_LOG=error` or pass `rust_log="error"` in `ClientOptions`.

## LibXMTP bindings

This SDK uses [libxmtp](https://github.com/xmtp/libxmtp) Python bindings for core XMTP functionality including cryptography, networking, and protocol implementation.

**Minimum version**: 1.7.0-r3

## Documentation

- [XMTP Documentation](https://docs.xmtp.org/)
- [Build an XMTP Agent](https://docs.xmtp.org/agents/get-started/build-an-agent)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

Apache 2.0
