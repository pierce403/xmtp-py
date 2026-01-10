# xmtp-py TODO

Tracking progress for building Python SDKs that mirror the xmtp-js interfaces.

## libxmtp bindings

- [x] Survey libxmtp repo bindings (ffi/wasm) and QA tools diagram referencing Napi; no Python bindings found as of 2026-01-10
- [ ] Create Python bindings package (PyO3/maturin) for libxmtp >= 1.7.0-r3
- [ ] Verify binding API compatibility with node-bindings interface
- [ ] Document binding installation and setup

## python-sdk (core client)

### Infrastructure
- [x] Set up package structure (`sdks/python-sdk/`)
- [x] Configure pyproject.toml with dependencies
- [x] Set up pytest for testing
- [x] Configure mypy for type checking

### Scaffolding
- [x] Create stub modules for core classes, signers, and utilities under `sdks/python-sdk/src/xmtp/`

### Core classes
- [ ] `Client` - Main client for interacting with XMTP network
  - [ ] `Client.create(signer, options)` - Create client with signer
  - [ ] `Client.build(identifier, options)` - Create client with identifier
  - [ ] Properties: `inbox_id`, `installation_id`, `is_registered`, `conversations`, `preferences`
  - [ ] Methods: `register()`, `can_message()`, `get_inbox_id_by_identifier()`
- [ ] `Conversations` - Conversation management
  - [ ] `new_dm()` / `new_dm_with_identifier()`
  - [ ] `new_group()` / `new_group_with_identifiers()`
  - [ ] `list()` / `list_dms()` / `list_groups()`
  - [ ] `get_conversation_by_id()`
  - [ ] `stream()` - Stream new conversations
  - [ ] `stream_all_messages()` - Stream all messages
  - [ ] `sync()` / `sync_all_conversations()`
- [ ] `Conversation` - Base conversation class
- [ ] `Dm` - Direct message conversation
- [ ] `Group` - Group conversation
  - [ ] Member management: `add_members()`, `remove_members()`, `members()`
  - [ ] Admin management: `add_admin()`, `remove_admin()`, `is_admin()`
  - [ ] Metadata: `name`, `description`, `image_url`
- [ ] `DecodedMessage` - Decoded message representation
- [ ] `Preferences` - User preferences management
- [ ] `AsyncStream` - Async iterator for streaming

### Signer support
- [ ] `Signer` protocol/interface
- [ ] EOA signer implementation
- [ ] SCW (Smart Contract Wallet) signer support
- [ ] Identifier types (Ethereum address, etc.)

### Types and utilities
- [ ] `XmtpEnv` type (`dev`, `production`)
- [ ] `ClientOptions` dataclass
- [ ] Error classes matching node-sdk errors
- [ ] Hex string validation utilities

## agent-sdk

### Infrastructure
- [x] Set up package structure (`sdks/agent-sdk/`)
- [x] Configure as separate installable package
- [x] Set up testing infrastructure

### Scaffolding
- [x] Create stub agent SDK modules under `sdks/agent-sdk/src/xmtp_agent/`

### Core classes
- [ ] `Agent` - Main agent class with EventEmitter pattern
  - [ ] `Agent.create(signer, options)` - Create agent
  - [ ] `Agent.create_from_env()` - Create from environment variables
  - [ ] `agent.start()` / `agent.stop()` - Lifecycle management
  - [ ] `agent.on(event, handler)` - Event registration
  - [ ] `agent.use(middleware)` - Middleware registration
  - [ ] `agent.errors.use(error_middleware)` - Error middleware

### Event system
- [ ] Message events: `text`, `reaction`, `reply`, `attachment`, `markdown`, `read-receipt`, `group-update`, `transaction-reference`, `wallet-send-calls`
- [ ] Conversation events: `conversation`, `dm`, `group`
- [ ] Lifecycle events: `start`, `stop`, `unhandled_error`
- [ ] `unknown_message` for unrecognized content types

### Context classes
- [ ] `MessageContext` - Context for message handlers
  - [ ] `send_text()`, `send_text_reply()`, `send_markdown()`, `send_reaction()`
  - [ ] Access to `message`, `conversation`, `client`
- [ ] `ConversationContext` - Context for conversation handlers
- [ ] `ClientContext` - Context for lifecycle handlers

### Middleware system
- [ ] Standard middleware chain (next() pattern)
- [ ] Error middleware chain
- [ ] Built-in `CommandRouter` middleware

### Filters
- [ ] `filter.is_text()`, `filter.is_reaction()`, etc.
- [ ] `filter.from_self()`, `filter.has_content()`
- [ ] Type guards for content type checking

### Utilities
- [ ] `create_user()` / `create_signer()` helpers
- [ ] `create_name_resolver()` for ENS/web3 name resolution
- [ ] Debug utilities: `get_test_url()`, `log_details()`
- [ ] Attachment utilities: `download_remote_attachment()`

## Content types

### Primitives
- [ ] `ContentCodec` protocol
- [ ] `ContentTypeId` class
- [ ] `EncodedContent` type
- [ ] Base codec implementation

### Individual content types
- [ ] `TextCodec` - Plain text messages
- [ ] `ReactionCodec` - Message reactions
- [ ] `ReplyCodec` - Message replies
- [ ] `ReadReceiptCodec` - Read receipts
- [ ] `RemoteAttachmentCodec` - Remote file attachments
- [ ] `AttachmentCodec` - Local attachments
- [ ] `MarkdownCodec` - Markdown messages
- [ ] `GroupUpdatedCodec` - Group update notifications
- [ ] `TransactionReferenceCodec` - On-chain transaction references
- [ ] `WalletSendCallsCodec` - Wallet transaction requests

## Environment variables

Support for configuration via environment:
- [ ] `XMTP_ENV` - Network environment (dev/production)
- [ ] `XMTP_WALLET_KEY` - Private key for wallet
- [ ] `XMTP_DB_DIRECTORY` - Database directory path
- [ ] `XMTP_DB_ENCRYPTION_KEY` - Database encryption key
- [ ] `XMTP_FORCE_DEBUG` - Enable debug logging
- [ ] `XMTP_FORCE_DEBUG_LEVEL` - Debug log level

## Testing

- [ ] Unit tests for all core classes
- [ ] Integration tests against XMTP dev network
- [ ] Test fixtures and helpers
- [ ] CI/CD pipeline setup

## Documentation

- [ ] API reference documentation
- [ ] Migration guide from xmtp-js
- [ ] Example applications
- [ ] Contributing guidelines

---

## Notes

- Target libxmtp version: >= 1.7.0-r3 (nothing from 1.6.x line)
- Interface parity with xmtp-js is the goal
- Python-idiomatic API where it makes sense (snake_case, async/await patterns)
- The `code/` directory contains xmtp-js reference code (not part of this repo)
