# xmtp-py

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

### From source (recommended until PyPI release)

Clone the repo and install into a virtualenv. You must install the bindings
and content types in the same environment before the SDK:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip

pip install -e bindings/python
pip install -e content-types/content-type-primitives
for pkg in content-types/*; do
  if [ "$pkg" != "content-types/content-type-primitives" ]; then
    pip install -e "$pkg"
  fi
done

# Choose one SDK:
pip install -e sdks/python-sdk
# or:
pip install -e sdks/agent-sdk
```

## Quick start

### Python SDK

```python
from xmtp import Client
from xmtp.signers import create_signer
from xmtp.types import ClientOptions

# Create a signer from a private key
signer = create_signer(private_key)

# Create the client
client = await Client.create(signer, ClientOptions(env='dev'))

# Create a conversation
dm = await client.conversations.new_dm("0x...")
await dm.send("Hello from Python!")

# Stream messages
async for message in client.conversations.stream_all_messages():
    print(f"Received: {message.content}")
```

### Agent SDK

```python
from xmtp.agent import Agent
from xmtp.agent.user import create_user, create_signer
from xmtp.types import ClientOptions

# Create a user and signer
user = create_user()
signer = create_signer(user)

# Create the agent
agent = await Agent.create(signer, ClientOptions(env='dev', db_path=None))

# Handle text messages
@agent.on("text")
async def handle_text(ctx):
    await ctx.send_text("Hello from my XMTP Agent! 👋")

# Start the agent
await agent.start()
```

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
