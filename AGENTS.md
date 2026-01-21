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

- As of 2026-01-10, libxmtp repo ships ffi/wasm bindings and QA tools diagrams reference Napi; Python bindings are built via UniFFI against `bindings_ffi`.
- Agent SDK is scaffolded under `xmtp_agent` for now; decide later if we move to a shared `xmtp.agent` namespace.
- Docstrings are wired into Sphinx autodoc (with napoleon + autodoc-typehints), and static typing is strict (mypy/pyright + ruff ANN rules).
- Python bindings now use UniFFI via libxmtp `bindings_ffi`; generate in `bindings/python` and keep native libs out of git.
- `FfiContentTypeId.__str__` is not the canonical content type string; convert to `ContentTypeId` and use its `__str__` for comparisons.
- CI runners do not ship `libxmtpv3.so`; `xmtp_bindings` raises `ImportError` when the native library is missing, and `xmtp.bindings` provides a stub that tests can monkeypatch.
- CI should set `XMTP_BINDINGS_SKIP_BUILD=1` to avoid attempting a Rust build of libxmtp during installs.
- `sdks/python-sdk/tests/conftest.py` installs a fake `xmtp_bindings.xmtpv3` module when native bindings are unavailable so content-type and bindings smoke tests still run.
- As of 2026-01-13, agent SDK key lifecycle is caller-owned: `create_user()` generates an in-memory key if none provided, `create_signer()` just wraps a key, and `Agent.create_from_env()` only reads `XMTP_WALLET_KEY` without any persistence or rotation helpers.
- xmtp-js agent-sdk mirrors this: `createUser()`/`createSigner()` are in-memory helpers, `Agent.createFromEnv()` reads `XMTP_WALLET_KEY` (expects 0x hex), and key generation lives in the `xmtp-cli keys` command rather than the SDK.
- History sync can be disabled via `ClientOptions.disable_history_sync` or `XMTP_DISABLE_HISTORY_SYNC`; endpoint overrides via `XMTP_API_URL`, `XMTP_HISTORY_SYNC_URL`, and `XMTP_GATEWAY_HOST`.
- `xmtp-bindings` now builds libxmtp during install via setuptools cmdclasses; requires `cargo` + `git` and honors `XMTP_LIBXMTP_*` env overrides.
- `bindings/python/pyproject.toml` cmdclass entries must use dotted paths (e.g., `xmtp_bindings.build.BuildPy`), not `module:Class`.
- Coverage omits `xmtp_bindings/build.py` because it is an install-time helper that is hard to exercise in unit tests.
- Mypy strict ignores `xmtp_bindings.build` and `xmtp_bindings.xmtpv3` via `pyproject.toml` overrides; content-type `_bindings()` helpers return `Any` and use casts where needed to avoid `no-any-return`.
- Mypy requires Protocol `__init__` signatures and explicit `cast()` when returning the `xmtp_bindings.xmtpv3` module from content-type `_bindings()` helpers; otherwise it flags incompatible return types and unexpected keyword arguments.
- `Client.prepare_for_send()` now mirrors xmtp-js send options by using codec `should_push`, and `Conversation.send()` uses it for non-text content.
- Agent SDK includes `resolve_recipient()` (ENS/address/inbox ID) and `backoff_reconnect()` helper plus `test_utils` for mock streams/record-replay.
- Packaging: root `pyproject.toml` defines the `xmtp` distribution, bundling `xmtp`, `xmtp_agent`, and all content types; `xmtp-bindings` remains a separate dist.
- Packaging: keep root `pyproject.toml` using `[tool.setuptools.package-dir]` (not an inline `package-dir = { ... }` table) to avoid TOML parse errors during `pip install -e`.
- Bindings build helper expects `_project_root()` to resolve to `bindings/python` (use `parents[2]` from `build.py`) so sdist/cibuildwheel builds can find `src/xmtp_bindings`.
- CIBW requires `CIBW_REPAIR_WHEEL_COMMAND_LINUX` to emit a wheel into `{dest_dir}`; if skipping auditwheel, use `cp {wheel} {dest_dir}` instead of `true`.
- CIBW aarch64 manylinux builds on GitHub Ubuntu runners can fail with `exec format error` unless QEMU/binfmt is set up; limit `CIBW_ARCHS_LINUX` or add QEMU.
- macOS x86_64 wheel builds on arm64 runners can fail delocate’s arch check; limit `CIBW_ARCHS_MACOS` or set up proper cross-builds/universal2.
- PyPI trusted publishing requires the GitHub Actions environment to match the configured publisher; missing/mismatched environment triggers `invalid-publisher` during publish.
- PyPI OIDC uploads cannot create new projects; the first release for each distribution must be created with a user/token or an existing project.
- PyPI rejects wheels tagged `linux_x86_64`; Linux wheels must be repaired to a manylinux tag (auditwheel) before upload.
- Auditwheel will fail if shared libraries are packaged under purelib; for bindings, set `build_py.build_lib` to `build_platlib` so `.so` lands in platlib.
- As of 2026-01-21, the PyPI project `xmtp` is configured as a Trusted Publisher for repo `pierce403/xmtp-py`, workflow `publish.yml`, environment `pypi`.
- When re-tagging the same version after partial PyPI uploads, set `skip-existing: true` in the publish action to avoid file-name reuse errors.

## Agent tips

- Always check `TODO.md` before starting work to see what's done
- If you edit `TODO.md`, make a commit and push as part of the same task
- Never write files outside the repo working directory (no `/tmp` writes); keep all artifacts within the project tree.
- LLM reference files live in `llms/` and are generated via `scripts/generate_llms.py`; regenerate after API/docs changes to satisfy CI `--check`
- CI enforces 100% branch coverage with pytest-cov and `.coveragerc`; `xmtp_bindings/xmtpv3.py` is omitted but bindings smoke tests are required
- CI runs ruff with `ANN`, `I`, and `UP` rules; avoid `Any`, import abstract types from `collections.abc`, and keep imports isort-ordered
- Pytest runs with `--import-mode=importlib`; keep `sdks/python-sdk/tests` without `__init__.py` to avoid `tests.conftest` collisions
- The xmtp-js reference in `code/` is comprehensive—use it
- libxmtp Python bindings may not exist yet; this is a key first step
- When in doubt about interface design, match xmtp-js closely

## Collaborator preferences

- Project must remain Apache 2.0 licensed.
- Always commit and push after every update.
