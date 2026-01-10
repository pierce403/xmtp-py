# xmtp-py TODO

All previously queued test parity + coverage tasks are complete.
Add new work items below as needed.

---

## Notes

- Test parity map: `docs/test_parity.rst`
- Coverage: pytest-cov with `.coveragerc`, CI fail-under 100, HTML/XML artifacts
- Bindings: smoke tests live in `sdks/python-sdk/tests/test_bindings_smoke.py`; generated `xmtp_bindings/xmtpv3.py` is omitted from coverage
- Rust/FFI coverage guidance is documented in `docs/contributing.rst`
- Target libxmtp version: >= 1.7.0-r3 (nothing from 1.6.x line)
- Interface parity with xmtp-js is the goal
- Python-idiomatic API where it makes sense (snake_case, async/await patterns)
- The `code/` directory contains xmtp-js reference code (not part of this repo)
