# AGENTS.md

Instructions for coding agents working on xmtp-py.

## 🔄 Self-improvement directive

**Update this file** whenever you learn something important about the project—wins, mistakes, conventions discovered, or collaborator preferences. Your learnings help future agents work more effectively.

## Project overview

**xmtp-py** is an unofficial Python SDK for the XMTP messaging network. It mirrors the structure and interfaces of the official [xmtp-js](https://github.com/xmtp/xmtp-js) SDK.

### Goals

- Feature parity with xmtp-js SDKs (node-sdk, agent-sdk)
- Python-idiomatic API (snake_case, async/await, type hints)
- libxmtp bindings >= 1.7.0-r3 (nothing from 1.6.x line)

### Key directories

```
xmtp-py/
├── AGENTS.md           # You are here
├── README.md           # Project overview
├── TODO.md             # Implementation checklist
├── code/               # xmtp-js reference (gitignored, not part of repo)
│   └── xmtp-js/        # Official JS SDK for reference
├── sdks/               # (to be created)
│   ├── python-sdk/     # Core XMTP client
│   └── agent-sdk/      # Event-driven agent framework
└── content-types/      # (to be created)
```

## Reference code

The `code/` directory contains a clone of xmtp-js for reference. It is **gitignored** and not part of this repository.

Key reference files:
- `code/xmtp-js/sdks/node-sdk/src/Client.ts` - Core client implementation
- `code/xmtp-js/sdks/node-sdk/src/Conversations.ts` - Conversation management
- `code/xmtp-js/sdks/agent-sdk/src/core/Agent.ts` - Agent class with event system
- `code/xmtp-js/sdks/agent-sdk/src/core/filter.ts` - Message type filters

## Code style

- Python 3.10+ required
- Use `snake_case` for functions, methods, variables
- Use `PascalCase` for classes
- Type hints on all public APIs
- Async/await for all network operations
- Docstrings in Google style
- Single quotes for strings (when no preference exists)

## Build & test commands

```bash
# (to be configured)
pip install -e ".[dev]"    # Install in dev mode
pytest                      # Run tests
mypy .                      # Type checking
ruff check .                # Linting
ruff format .               # Formatting
```

## Implementation approach

1. Check `TODO.md` for current implementation status
2. Reference the corresponding xmtp-js code for interface design
3. Adapt to Python idioms while maintaining API compatibility
4. Write tests alongside implementation

## Naming conventions (JS → Python)

| JavaScript | Python |
|------------|--------|
| `newDm()` | `new_dm()` |
| `streamAllMessages()` | `stream_all_messages()` |
| `inboxId` | `inbox_id` |
| `ContentTypeId` | `ContentTypeId` (classes stay PascalCase) |
| `async/await` | `async/await` |
| `null` | `None` |
| `undefined` | `None` or omit |

## Known issues & solutions

- As of 2026-01-10, libxmtp repo ships ffi/wasm bindings and QA tools diagrams reference Napi, but no Python bindings; plan to build with PyO3/maturin.
- Agent SDK is scaffolded under `xmtp_agent` for now; decide later if we move to a shared `xmtp.agent` namespace.
- Docstrings are wired into Sphinx autodoc (with napoleon + autodoc-typehints), and static typing is strict (mypy/pyright + ruff ANN rules).

## Agent tips

- Always check `TODO.md` before starting work to see what's done
- If you edit `TODO.md`, make a commit and push as part of the same task
- The xmtp-js reference in `code/` is comprehensive—use it
- libxmtp Python bindings may not exist yet; this is a key first step
- When in doubt about interface design, match xmtp-js closely

## Collaborator preferences

- Project must remain Apache 2.0 licensed.
