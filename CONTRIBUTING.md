# Contributing

Thanks for your interest in contributing to xmtp-py!

## Quick start

- Use Python 3.10+.
- Install dependencies:

```bash
pip install -e bindings/python
pip install -e content-types/content-type-primitives
pip install -e content-types/content-type-text
pip install -e content-types/content-type-markdown
pip install -e content-types/content-type-reaction
pip install -e content-types/content-type-read-receipt
pip install -e content-types/content-type-reply
pip install -e content-types/content-type-remote-attachment
pip install -e content-types/content-type-group-updated
pip install -e content-types/content-type-transaction-reference
pip install -e content-types/content-type-wallet-send-calls
pip install -e sdks/python-sdk[dev]
pip install -e sdks/agent-sdk[dev]
```

## Testing

```bash
pytest sdks/python-sdk/tests
pytest sdks/agent-sdk/tests
```

Integration tests can be enabled by setting:

```bash
export XMTP_INTEGRATION_TESTS=1
export XMTP_WALLET_KEY=0x...
```

## Linting and typing

```bash
ruff check sdks/python-sdk/src sdks/agent-sdk/src content-types
mypy sdks/python-sdk/src sdks/agent-sdk/src
```

## Notes

- Update `TODO.md` as progress is made, and commit + push when it changes.
- Use the xmtp-js reference in `code/` to keep APIs aligned.
