# xmtp-py TODO

Tracking progress for building Python SDKs that mirror the xmtp-js interfaces.

## libxmtp bindings

- [x] Survey libxmtp repo bindings (ffi/wasm) and QA tools diagram referencing Napi; no Python bindings found as of 2026-01-10
- [x] Create Python bindings package (UniFFI-based) for libxmtp >= 1.7.0-r3
- [x] Verify binding API compatibility with node-bindings interface
- [x] Document binding installation and setup

## python-sdk (core client)

### Infrastructure
- [x] Set up package structure (`sdks/python-sdk/`)
- [x] Configure pyproject.toml with dependencies
- [x] Set up pytest for testing
- [x] Configure mypy for type checking

### Scaffolding
- [x] Create stub modules for core classes, signers, and utilities under `sdks/python-sdk/src/xmtp/`

### Core classes
- [x] `Client` - Main client for interacting with XMTP network
  - [x] `Client.create(signer, options)` - Create client with signer
  - [x] `Client.build(identifier, options)` - Create client with identifier
  - [x] Properties: `inbox_id`, `installation_id`, `is_registered`, `conversations`, `preferences`
  - [x] Methods: `register()`, `can_message()`, `get_inbox_id_by_identifier()`
- [x] `Conversations` - Conversation management
  - [x] `new_dm()` / `new_dm_with_identifier()`
  - [x] `new_group()` / `new_group_with_identifiers()`
  - [x] `list()` / `list_dms()` / `list_groups()`
  - [x] `get_conversation_by_id()`
  - [x] `stream()` - Stream new conversations
  - [x] `stream_all_messages()` - Stream all messages
  - [x] `sync()` / `sync_all_conversations()`
- [x] `Conversation` - Base conversation class
- [x] `Dm` - Direct message conversation
- [x] `Group` - Group conversation
  - [x] Member management: `add_members()`, `remove_members()`, `members()`
  - [x] Admin management: `add_admin()`, `remove_admin()`, `is_admin()`
  - [x] Metadata: `name`, `description`, `image_url`
- [x] `DecodedMessage` - Decoded message representation
- [x] `Preferences` - User preferences management
- [x] `AsyncStream` - Async iterator for streaming

### Signer support
- [x] `Signer` protocol/interface
- [x] EOA signer implementation
- [x] SCW (Smart Contract Wallet) signer support
- [x] Identifier types (Ethereum address, etc.)

### Types and utilities
- [x] `XmtpEnv` type (`dev`, `production`)
- [x] `ClientOptions` dataclass
- [x] Error classes matching node-sdk errors
- [x] Hex string validation utilities

## agent-sdk

### Infrastructure
- [x] Set up package structure (`sdks/agent-sdk/`)
- [x] Configure as separate installable package
- [x] Set up testing infrastructure

### Scaffolding
- [x] Create stub agent SDK modules under `sdks/agent-sdk/src/xmtp_agent/`

### Core classes
- [x] `Agent` - Main agent class with EventEmitter pattern
  - [x] `Agent.create(signer, options)` - Create agent
  - [x] `Agent.create_from_env()` - Create from environment variables
  - [x] `agent.start()` / `agent.stop()` - Lifecycle management
  - [x] `agent.on(event, handler)` - Event registration
  - [x] `agent.use(middleware)` - Middleware registration
  - [x] `agent.errors.use(error_middleware)` - Error middleware

### Event system
- [x] Message events: `text`, `reaction`, `reply`, `attachment`, `markdown`, `read-receipt`, `group-update`, `transaction-reference`, `wallet-send-calls`
- [x] Conversation events: `conversation`, `dm`, `group`
- [x] Lifecycle events: `start`, `stop`, `unhandled_error`
- [x] `unknown_message` for unrecognized content types

### Context classes
- [x] `MessageContext` - Context for message handlers
  - [x] `send_text()`, `send_text_reply()`, `send_markdown()`, `send_reaction()`
  - [x] Access to `message`, `conversation`, `client`
- [x] `ConversationContext` - Context for conversation handlers
- [x] `ClientContext` - Context for lifecycle handlers

### Middleware system
- [x] Standard middleware chain (next() pattern)
- [x] Error middleware chain
- [x] Built-in `CommandRouter` middleware

### Filters
- [x] `filter.is_text()`, `filter.is_reaction()`, etc.
- [x] `filter.from_self()`, `filter.has_content()`
- [x] Type guards for content type checking

### Utilities
- [x] `create_user()` / `create_signer()` helpers
- [x] `create_name_resolver()` for ENS/web3 name resolution
- [x] Debug utilities: `get_test_url()`, `log_details()`
- [x] Attachment utilities: `download_remote_attachment()`

## Content types

### Primitives
- [x] `ContentCodec` protocol
- [x] `ContentTypeId` class
- [x] `EncodedContent` type
- [x] Base codec implementation

### Individual content types
- [x] `TextCodec` - Plain text messages
- [x] `ReactionCodec` - Message reactions
- [x] `ReplyCodec` - Message replies
- [x] `ReadReceiptCodec` - Read receipts
- [x] `RemoteAttachmentCodec` - Remote file attachments
- [x] `AttachmentCodec` - Local attachments
- [x] `MarkdownCodec` - Markdown messages
- [x] `GroupUpdatedCodec` - Group update notifications
- [x] `TransactionReferenceCodec` - On-chain transaction references
- [x] `WalletSendCallsCodec` - Wallet transaction requests

## Environment variables

Support for configuration via environment:
- [x] `XMTP_ENV` - Network environment (dev/production)
- [x] `XMTP_WALLET_KEY` - Private key for wallet
- [x] `XMTP_DB_DIRECTORY` - Database directory path
- [x] `XMTP_DB_ENCRYPTION_KEY` - Database encryption key
- [x] `XMTP_FORCE_DEBUG` - Enable debug logging
- [x] `XMTP_FORCE_DEBUG_LEVEL` - Debug log level

## Testing

- [x] Unit tests for all core classes
- [x] Integration tests against XMTP dev network
- [x] Test fixtures and helpers
- [x] CI/CD pipeline setup

## Documentation

- [x] API reference documentation
- [x] Migration guide from xmtp-js
- [x] Example applications
- [x] Contributing guidelines

## Tooling

- [x] Enable strict type checking (mypy/pyright) and typing lint rules (ruff)
- [x] Set up Sphinx autodoc for docstring-generated docs

---

## Notes

- Target libxmtp version: >= 1.7.0-r3 (nothing from 1.6.x line)
- Interface parity with xmtp-js is the goal
- Python-idiomatic API where it makes sense (snake_case, async/await patterns)
- The `code/` directory contains xmtp-js reference code (not part of this repo)
