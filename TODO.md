# xmtp-py TODO

All previously queued test parity + coverage tasks are complete.
Add new work items below as needed.

---

## CI fixes (2026-01-21)

- [x] Replace `Any` annotations in content-type `_bindings` helpers with Protocols to satisfy ruff ANN401
- [x] Fix import ordering in content-type modules flagged by ruff
- [x] Address ruff UP037 forward-reference cleanup and missing Any import in content-type reply/group-updated
- [x] Add Protocol __init__ signatures + casted binding modules to satisfy mypy for content-type FFI helpers
- [x] Fix mypy no-any-return in agent attachment fetch
- [x] Stabilize backoff reconnect timing + add tests to cover error/recipient branches for 100% coverage
- [x] Make backoff reconnect time mock infinite to avoid StopIteration during teardown
- [x] Regenerate llms reference files after API/type updates
- [x] Make CI coverage artifact name unique per OS to avoid upload conflicts
- [x] Make CI pytest command PowerShell-friendly on Windows

## Release workflow fixes (2026-01-21)

- [x] Install perl-IPC-Cmd in manylinux before building bindings wheels to fix openssl-sys
- [x] Install perl-Time-Piece in manylinux to satisfy OpenSSL build dependencies
- [x] Mark bindings wheel as platform-specific to avoid pure-Python wheel rejection
- [x] Force Root-Is-Purelib false in bindings wheel metadata for auditwheel
- [x] Skip auditwheel repair in release build while platlib placement is unresolved
- [x] Ensure cibuildwheel repair step copies wheels to {dest_dir} when auditwheel is skipped
- [x] Temporarily limit Linux wheels to x86_64 to avoid aarch64 exec format errors
- [x] Temporarily limit macOS wheels to arm64 to avoid delocate arch mismatch on x86_64
- [x] Add `publish` job environment to align with PyPI trusted publisher claims
- [x] Set PyPI publish `skip-existing` to handle retries after partial uploads
- [x] Re-enable auditwheel repair so Linux wheels publish with manylinux tags (PyPI rejects `linux_x86_64`)
- [x] Force bindings install to platlib (install_lib=install_platlib) so auditwheel sees shared libs
- [x] Regenerate UniFFI bindings during builds so `xmtpv3.py` always matches built libxmtp
- [x] Auto-detect libxmtp UniFFI bindgen directory (bindings_ffi vs bindings/ffi) during builds

## Client/API fixes (2026-01-22)

- [x] Resolve inbox IDs before creating DMs and fall back across libxmtp DM creation APIs
- [x] Add conversation tests covering inbox-id DM creation and legacy fallbacks
- [x] Pin libxmtp release tag for bindings builds via `libxmtp.ref` (swift-bindings-1.9.0.d206831)
- [x] Add DM tests for `find_or_create_dm_by_identity` fallback variants
- [x] Cover DM fallback TypeErrors and send-options fallback to satisfy 100% coverage

## Docs/LLM updates (2026-01-22)

- [x] Regenerate `llms/*.txt` after release/checklist guidance updates

## Release prep (2026-01-22)

- [x] Bump package versions to 0.1.4 before tagging

## Defaults & docs (2026-01-22)

- [x] Disable history sync by default in `ClientOptions` and allow env overrides to re-enable
- [x] Update docs/examples to prefer Agent SDK and note history sync defaults
- [x] Note xmtp-js dbPath default + sqlite sidecar files in AGENTS
- [x] Update README quick start examples (agent + client) to send "Hello from xmtp-py <version>" directly (async main + asyncio.run)
- [x] Remove stray top-level await from README agent example
- [x] Add LogLevel.OFF to match xmtp-js log level list
- [x] Add ClientOptions.rust_log + XMTP_RUST_LOG env hook (default off)

## PyPI release checklist

- [x] Reserve project name on PyPI: `xmtp` (exists)
- [ ] Reserve project name on PyPI: `xmtp-bindings`
- [x] Enable Trusted Publishing (OIDC) for PyPI project `xmtp` (repo `pierce403/xmtp-py`, workflow `publish.yml`, env `pypi`)
- [ ] Enable Trusted Publishing (OIDC) for PyPI project `xmtp-bindings`
- [ ] Create initial PyPI project `xmtp-bindings` with a user/token upload (OIDC cannot create new projects)
- [ ] Run packaging QA locally: `python -m build` for root + bindings, then `twine check`
- [ ] Install built wheels in a clean venv and run `sdks/python-sdk/tests/test_smoke_imports.py`
- [ ] Verify GitHub Actions release workflow publishes both `xmtp` and `xmtp-bindings`
- [ ] Document final release confirmation steps in `docs/release.md` if needed

## Notes

- Test parity map: `docs/test_parity.rst`
- Coverage: pytest-cov with `.coveragerc`, CI fail-under 100, HTML/XML artifacts
- Bindings: smoke tests live in `sdks/python-sdk/tests/test_bindings_smoke.py`; generated `xmtp_bindings/xmtpv3.py` is omitted from coverage
- Rust/FFI coverage guidance is documented in `docs/contributing.rst`
- Target libxmtp version: >= 1.7.0-r3 (nothing from 1.6.x line)
- Interface parity with xmtp-js is the goal
- Python-idiomatic API where it makes sense (snake_case, async/await patterns)
- The `code/` directory contains xmtp-js reference code (not part of this repo)
