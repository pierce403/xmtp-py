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

## PyPI release checklist

- [ ] Reserve project names on PyPI + TestPyPI: `xmtp` and `xmtp-bindings`
- [ ] Enable Trusted Publishing (OIDC) for both PyPI projects
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
