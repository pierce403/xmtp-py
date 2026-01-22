# Release checklist

This repo publishes two distributions:

- `xmtp` (Python SDK + agent SDK + content types)
- `xmtp-bindings` (native libxmtp bindings)

## Versioning

- Use PEP 440 versions (e.g. `0.1.0`, `0.1.1`, `0.2.0rc1`).
- Keep `pyproject.toml` versions in sync for `xmtp` and `bindings/python`.
- Update `__version__` in `sdks/python-sdk/src/xmtp/__init__.py` and
  `sdks/agent-sdk/src/xmtp_agent/__init__.py`.

## Pre-release checks (local)

Create a clean venv and run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip build twine

# Bindings
python -m build bindings/python

# SDK
python -m build .

twine check dist/* bindings/python/dist/*

# DM API compatibility check (ensures bindings/SDK signatures match)
python -m pytest sdks/python-sdk/tests/test_conversations.py -k new_dm
```

Smoke test install:

```bash
python -m venv /tmp/xmtp-smoke
source /tmp/xmtp-smoke/bin/activate
python -m pip install -U pip

# Install bindings (prebuilt wheel preferred)
python -m pip install xmtp-bindings

# Install SDK
python -m pip install xmtp

python - <<'PY'
from xmtp import Client, ClientOptions
from xmtp_agent import Agent
from xmtp_content_type_text import TextCodec

ClientOptions()
TextCodec()
print('smoke ok')
PY
```

## Release steps

1. Bump versions (PEP 440) in:
   - `pyproject.toml`
   - `bindings/python/pyproject.toml`
   - `sdks/python-sdk/src/xmtp/__init__.py`
   - `sdks/agent-sdk/src/xmtp_agent/__init__.py`
2. Update `bindings/python/src/xmtp_bindings/libxmtp.ref` if pinning a new libxmtp commit.
3. Update `CHANGELOG` (if added later).
4. Commit and push.
5. Ensure the latest `ci.yml` workflow run on `main` is green.
6. Tag the release: `git tag vX.Y.Z && git push origin vX.Y.Z`.
7. GitHub Actions `Release` workflow builds and publishes to PyPI via Trusted Publishing.
8. Verify the release on PyPI and run the smoke test in a clean environment.

## TestPyPI (optional)

Use the TestPyPI workflow (manual) to validate packaging before a real release.
