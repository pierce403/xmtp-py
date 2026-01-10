Contributing
============

See the repository's ``CONTRIBUTING.md`` for setup, testing, and linting notes.

Testing and coverage
--------------------

This repo enforces full branch coverage for the Python SDKs and content types.
We exclude generated UniFFI glue (``xmtp_bindings/xmtpv3.py``) from coverage
because it is machine-generated, but we still exercise bindings via smoke tests.

Run tests with coverage locally:

.. code-block:: bash

   pytest \\
     --cov=sdks/python-sdk/src \\
     --cov=sdks/agent-sdk/src \\
     --cov=content-types \\
     --cov=bindings/python/src \\
     --cov-branch \\
     --cov-report=term-missing:skip-covered \\
     --cov-report=xml \\
     --cov-report=html \\
     --cov-config=.coveragerc

FFI/Rust coverage (libxmtp)
---------------------------

Rust coverage lives in the libxmtp repo, not this one. To measure it, run
``cargo llvm-cov`` in the libxmtp workspace (example):

.. code-block:: bash

   cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info
