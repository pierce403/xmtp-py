# xmtp-py TODO

Current open work to keep parity with xmtp-js and enforce full coverage.

## Test parity with xmtp-js

- [ ] Map xmtp-js test suites to Python equivalents and track coverage parity
  - [ ] Content types tests (text, markdown, reaction, reply, read-receipt, group-updated, remote-attachment, transaction-reference, wallet-send-calls, primitives)
  - [ ] python-sdk tests (Client, Conversations, Conversation, Preferences, AsyncStream, validation/inbox ID, debug info)
  - [ ] agent-sdk tests (Agent, MessageContext, filters, CommandRouter, AttachmentUtil, NameResolver)
- [ ] Implement missing Python tests to match xmtp-js behavior 1:1

## Coverage

- [ ] Add coverage tooling (pytest-cov + config) for python-sdk, agent-sdk, content-types
- [ ] Add coverage reporting in CI and fail if coverage < 100%
- [ ] Add binding-level coverage targets (generate tests that exercise xmtp-bindings code paths)
- [ ] Investigate Rust/FFI coverage for libxmtp (e.g., cargo llvm-cov) and document how to run it
- [ ] Document coverage strategy (branch vs line, excludes, and why)
- [ ] Add a coverage dashboard/report artifact (HTML + XML) for CI visibility

---

## Notes

- Coverage tracking is not wired up yet; we need pytest-cov + CI fail-under plus bindings/FFI coverage guidance.
- Maximize coverage by: using branch coverage, avoiding blanket excludes, adding regression tests for error paths, and ensuring each public API path is exercised (including bindings wrappers).
- Target libxmtp version: >= 1.7.0-r3 (nothing from 1.6.x line)
- Interface parity with xmtp-js is the goal
- Python-idiomatic API where it makes sense (snake_case, async/await patterns)
- The `code/` directory contains xmtp-js reference code (not part of this repo)
